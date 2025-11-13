# Cluster 50

def simple_repr(record: Any) -> str:
    """
    Simple renderer for a SQL table
    :param record: A table record.
    :return: A string description of the record.
    """
    out = '{:28}: {}\n'.format('token', record.token)
    columns = None
    if hasattr(record, '__table__'):
        columns = {c for c in record.__table__.columns.keys()}
    for field, value in vars(record).items():
        if columns and field not in columns:
            continue
        if not (field[0] == '_' or field == 'token'):
            out += '{:28}: {}\n'.format(field, value)
    return out + '\n'

def _get_public_methods(class_type: Type[Any], only_abstract: bool) -> Dict[str, Callable[..., Any]]:
    """
    Get all of the public methods exposed on a class.
    This excludes magic methods and underscore-prefixed methods.
    :param class_type: The type of the class for which to get the methods.
    :param only_abstract: If true, only returns abstract methods.
    :return: Mapping of (method_name -> function_object).
    """
    all_functions = {tup[0]: tup[1] for tup in inspect.getmembers(class_type, predicate=inspect.isfunction) if tup[1].__qualname__.startswith(class_type.__qualname__)}
    public_functions = {key: all_functions[key] for key in all_functions if not key.startswith('_')}
    if only_abstract:
        public_functions = {key: public_functions[key] for key in public_functions if hasattr(public_functions[key], '__isabstractmethod__') and public_functions[key].__isabstractmethod__}
    return public_functions

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

def setUp(self) -> None:
    """Inherited, see superclass"""
    self.scenario = get_test_nuplan_scenario()
    self.planned_trajectory_samples = 10
    self.planner = MockIDMPlanner(target_velocity=10, min_gap_to_lead_agent=0.5, headway_time=1.5, accel_max=1.0, decel_max=2.0, planned_trajectory_samples=self.planned_trajectory_samples, planned_trajectory_sample_interval=0.2, occupancy_map_radius=20)

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

def setUp(self) -> None:
    """Inherited, see superclass"""
    self.scenario = get_test_nuplan_scenario()
    self.planned_trajectory_samples = 10
    self.planner = IDMPlanner(target_velocity=10, min_gap_to_lead_agent=0.5, headway_time=1.5, accel_max=1.0, decel_max=2.0, planned_trajectory_samples=self.planned_trajectory_samples, planned_trajectory_sample_interval=0.2, occupancy_map_radius=20)

class ModelLoader:
    """
    A class to load in an NNModel and prepare pytorch for inference.
    Used for simulating ML planners and smart agents throughout the nuPlan training framework.
    """

    def __init__(self, model: TorchModuleWrapper) -> None:
        """
        Initializes the ModelLoader class.
        :param model: Model to use for inference.
        """
        self.feature_builders = model.get_list_of_required_feature()
        self._model = model
        self._initialized = False

    def _initialize_torch(self) -> None:
        """
        Sets up torch/torchscript for inference.
        """
        torch.set_grad_enabled(False)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def _initialize_model(self) -> None:
        """
        Sets up the model.
        """
        self._model.eval()
        self._model = self._model.to(self.device)

    def initialize(self) -> None:
        """
        Initializes the ModelLoader
        """
        self._initialize_torch()
        self._initialize_model()
        self._initialized = True

    def build_features(self, current_input: PlannerInput, initialization: PlannerInitialization) -> FeaturesType:
        """
        Makes a single inference on a Pytorch/Torchscript model.
        :param current_input: Iteration specific inputs for building the feature.
        :param initialization: Additional data require for building the feature.
        :return: dictionary of FeaturesType types.
        """
        assert self._initialized, 'The model loader has not been initialized!'
        features = {builder.get_feature_unique_name(): builder.get_features_from_simulation(current_input, initialization) for builder in self.feature_builders}
        features = {name: feature.to_feature_tensor() for name, feature in features.items()}
        features = {name: feature.to_device(self.device) for name, feature in features.items()}
        features = {name: feature.collate([feature]) for name, feature in features.items()}
        return features

    def infer(self, features: FeaturesType) -> TargetsType:
        """
        Makes a single inference on a Pytorch/Torchscript model.

        :param features: dictionary of feature types
        :return: dictionary of target types
        """
        assert self._initialized is True, 'The model loader has not been initialized!'
        return self._model.forward(features)

def __init__(self, model: TorchModuleWrapper) -> None:
    """
        Initializes the ModelLoader class.
        :param model: Model to use for inference.
        """
    self.feature_builders = model.get_list_of_required_feature()
    self._model = model
    self._initialized = False

def construct_simple_vector_map_ml_planner() -> MLPlanner:
    """
    Construct vector map simple planner
    :return: MLPlanner with vector map model
    """
    future_trajectory_param = TrajectorySampling(time_horizon=6.0, num_poses=12)
    past_trajectory_param = TrajectorySampling(time_horizon=2.0, num_poses=4)
    model = VectorMapSimpleMLP(num_output_features=36, hidden_size=128, vector_map_feature_radius=20, past_trajectory_sampling=past_trajectory_param, future_trajectory_sampling=future_trajectory_param)
    return MLPlanner(model=model)

def construct_raster_ml_planner() -> MLPlanner:
    """
    Construct Raster ML Planner
    :return: MLPlanner with raster model
    """
    future_trajectory_param = TrajectorySampling(time_horizon=6.0, num_poses=12)
    model = RasterModel(model_name='resnet50', pretrained=True, num_input_channels=4, num_features_per_pose=3, future_trajectory_sampling=future_trajectory_param, feature_builders=[RasterFeatureBuilder(map_features={'LANE': 1.0, 'INTERSECTION': 1.0, 'STOP_LINE': 0.5, 'CROSSWALK': 0.5}, num_input_channels=4, target_width=224, target_height=224, target_pixel_size=0.5, ego_width=2.297, ego_front_length=4.049, ego_rear_length=1.127, ego_longitudinal_offset=0.0, baseline_path_thickness=1)], target_builders=[EgoTrajectoryTargetBuilder(future_trajectory_sampling=future_trajectory_param)])
    return MLPlanner(model=model)

def construct_urban_driver_open_loop_ml_planner() -> MLPlanner:
    """
    Construct UrbanDriverOpenLoop ML Planner
    :return: MLPlanner with urban_driver_open_loop model
    """
    model_params = UrbanDriverOpenLoopModelParams(local_embedding_size=256, global_embedding_size=256, num_subgraph_layers=3, global_head_dropout=0.0)
    feature_params = UrbanDriverOpenLoopModelFeatureParams(feature_types={'NONE': -1, 'EGO': 0, 'VEHICLE': 1, 'BICYCLE': 2, 'PEDESTRIAN': 3, 'LANE': 4, 'STOP_LINE': 5, 'CROSSWALK': 6, 'LEFT_BOUNDARY': 7, 'RIGHT_BOUNDARY': 8, 'ROUTE_LANES': 9}, total_max_points=20, feature_dimension=8, agent_features=['VEHICLE', 'BICYCLE', 'PEDESTRIAN'], ego_dimension=3, agent_dimension=8, max_agents=30, past_trajectory_sampling=TrajectorySampling(time_horizon=2.0, num_poses=4), map_features=['LANE', 'LEFT_BOUNDARY', 'RIGHT_BOUNDARY', 'STOP_LINE', 'CROSSWALK', 'ROUTE_LANES'], max_elements={'LANE': 30, 'LEFT_BOUNDARY': 30, 'RIGHT_BOUNDARY': 30, 'STOP_LINE': 20, 'CROSSWALK': 20, 'ROUTE_LANES': 30}, max_points={'LANE': 20, 'LEFT_BOUNDARY': 20, 'RIGHT_BOUNDARY': 20, 'STOP_LINE': 20, 'CROSSWALK': 20, 'ROUTE_LANES': 20}, vector_set_map_feature_radius=35, interpolation_method='linear', disable_map=False, disable_agents=False)
    target_params = UrbanDriverOpenLoopModelTargetParams(num_output_features=36, future_trajectory_sampling=TrajectorySampling(time_horizon=6.0, num_poses=12))
    model = UrbanDriverOpenLoopModel(model_params, feature_params, target_params)
    return MLPlanner(model=model)

class TestMlPlanner(unittest.TestCase):
    """
    Test MLPlanner with two models.
    """

    def setUp(self) -> None:
        """Inherited, see superclass."""
        self.scenario = get_test_nuplan_scenario()

    def test_simple_vector_net_model(self) -> None:
        """Test Model Vector Map Simple"""
        self.run_test_ml_planner(construct_simple_vector_map_ml_planner())

    def test_raster_net_model(self) -> None:
        """Test Raster Net model"""
        self.run_test_ml_planner(construct_raster_ml_planner())

    def test_urban_driver_open_loop_model(self) -> None:
        """Test UrbanDriverOpenLoop model"""
        self.run_test_ml_planner(construct_urban_driver_open_loop_ml_planner())

    def run_test_ml_planner(self, planner: MLPlanner) -> None:
        """Tests if progress is calculated correctly"""
        scenario = self.scenario
        simulation_history_buffer_duration = 2
        buffer_size = int(simulation_history_buffer_duration / self.scenario.database_interval + 1)
        history = SimulationHistoryBuffer.initialize_from_scenario(buffer_size=buffer_size, scenario=self.scenario, observation_type=DetectionsTracks)
        initialization = PlannerInitialization(route_roadblock_ids=scenario.get_route_roadblock_ids(), mission_goal=scenario.get_mission_goal(), map_api=scenario.map_api)
        planner.initialize(initialization)
        trajectory = planner.compute_trajectory(PlannerInput(iteration=SimulationIteration(index=0, time_point=scenario.start_time), history=history, traffic_light_data=list(scenario.get_traffic_light_status_at_iteration(0))))
        self.assertNotEqual(trajectory, None)
        self.assertEqual(len(trajectory.get_sampled_trajectory()), planner._num_output_dim + 1)

def setUp(self) -> None:
    """Inherited, see superclass."""
    self.scenario = get_test_nuplan_scenario()

class TestProfileIDM(unittest.TestCase):
    """
    Profiling test for IDM agents.
    """

    def setUp(self) -> None:
        """
        Inherited, see super class.
        """
        self.n_repeat_trials = 1
        self.display_results = True
        self.scenario = get_test_nuplan_scenario()

    def test_profile_idm_agent_observation(self) -> None:
        """Profile IDMAgents."""
        profiler = Profiler(interval=0.0001)
        profiler.start()
        for _ in range(self.n_repeat_trials):
            observation = IDMAgents(target_velocity=10, min_gap_to_lead_agent=0.5, headway_time=1.5, accel_max=1.0, decel_max=2.0, scenario=self.scenario, open_loop_detections_types=[])
            for step in range(self.scenario.get_number_of_iterations() - 1):
                iteration = SimulationIteration(time_point=self.scenario.get_time_point(step), index=step)
                next_iteration = SimulationIteration(time_point=self.scenario.get_time_point(step + 1), index=step + 1)
                buffer = SimulationHistoryBuffer.initialize_from_list(1, [self.scenario.get_ego_state_at_iteration(step)], [self.scenario.get_tracked_objects_at_iteration(step)], next_iteration.time_point.time_s - iteration.time_point.time_s)
                observation.update_observation(iteration, next_iteration, buffer)
        profiler.stop()
        if self.display_results:
            logger.info(profiler.output_text(unicode=True, color=True))

def setUp(self) -> None:
    """
        Inherited, see super class.
        """
    self.n_repeat_trials = 1
    self.display_results = True
    self.scenario = get_test_nuplan_scenario()

class TestTrajectorySampling(unittest.TestCase):
    """
    Test trajectory sampling parameters
    """

    def test_wrong_setup(self) -> None:
        """Raise in case the sampling args are not consistent."""
        with self.assertRaises(ValueError):
            TrajectorySampling(num_poses=10, time_horizon=8, interval_length=0.5)
        with self.assertRaises(ValueError):
            TrajectorySampling()
        with self.assertRaises(ValueError):
            TrajectorySampling(num_poses=10)
            TrajectorySampling(time_horizon=10)
            TrajectorySampling(interval_length=10)

    def test_num_poses(self) -> None:
        """Test that num poses are set correctly."""
        sampling = TrajectorySampling(time_horizon=8, interval_length=0.5)
        self.assertEqual(sampling.time_horizon, 8)
        self.assertEqual(sampling.interval_length, 0.5)
        self.assertEqual(sampling.num_poses, 16)

    def test_num_poses_floating(self) -> None:
        """Test that num poses are set correctly even with floating point numbers."""
        sampling = TrajectorySampling(time_horizon=0.5, interval_length=0.1)
        self.assertEqual(sampling.time_horizon, 0.5)
        self.assertEqual(sampling.interval_length, 0.1)
        self.assertEqual(sampling.num_poses, 5)

    def test_interval(self) -> None:
        """Test that interval are set correctly."""
        sampling = TrajectorySampling(time_horizon=8, num_poses=16)
        self.assertEqual(sampling.time_horizon, 8)
        self.assertEqual(sampling.interval_length, 0.5)
        self.assertEqual(sampling.num_poses, 16)

    def test_time_horizon(self) -> None:
        """Test that time_horizon are set correctly."""
        sampling = TrajectorySampling(interval_length=0.5, num_poses=16)
        self.assertEqual(sampling.time_horizon, 8)
        self.assertEqual(sampling.interval_length, 0.5)
        self.assertEqual(sampling.num_poses, 16)

def test_wrong_setup(self) -> None:
    """Raise in case the sampling args are not consistent."""
    with self.assertRaises(ValueError):
        TrajectorySampling(num_poses=10, time_horizon=8, interval_length=0.5)
    with self.assertRaises(ValueError):
        TrajectorySampling()
    with self.assertRaises(ValueError):
        TrajectorySampling(num_poses=10)
        TrajectorySampling(time_horizon=10)
        TrajectorySampling(interval_length=10)

def test_num_poses(self) -> None:
    """Test that num poses are set correctly."""
    sampling = TrajectorySampling(time_horizon=8, interval_length=0.5)
    self.assertEqual(sampling.time_horizon, 8)
    self.assertEqual(sampling.interval_length, 0.5)
    self.assertEqual(sampling.num_poses, 16)

def test_num_poses_floating(self) -> None:
    """Test that num poses are set correctly even with floating point numbers."""
    sampling = TrajectorySampling(time_horizon=0.5, interval_length=0.1)
    self.assertEqual(sampling.time_horizon, 0.5)
    self.assertEqual(sampling.interval_length, 0.1)
    self.assertEqual(sampling.num_poses, 5)

def test_interval(self) -> None:
    """Test that interval are set correctly."""
    sampling = TrajectorySampling(time_horizon=8, num_poses=16)
    self.assertEqual(sampling.time_horizon, 8)
    self.assertEqual(sampling.interval_length, 0.5)
    self.assertEqual(sampling.num_poses, 16)

def test_time_horizon(self) -> None:
    """Test that time_horizon are set correctly."""
    sampling = TrajectorySampling(interval_length=0.5, num_poses=16)
    self.assertEqual(sampling.time_horizon, 8)
    self.assertEqual(sampling.interval_length, 0.5)
    self.assertEqual(sampling.num_poses, 16)

def iterator_is_equal(a: Iterable[Any], b: Iterable[Any]) -> bool:
    """
    Checks that two iterables are equal by value.
    :param a: a in a == b.
    :param b: b in a == b.
    :return: true if the iterable contents match.
    """
    for a_item, b_item in zip((a_iter := iter(a)), (b_iter := iter(b))):
        if not objects_are_equal(a_item, b_item):
            return False
    try:
        next(a_iter)
        return False
    except StopIteration:
        try:
            next(b_iter)
            return False
        except StopIteration:
            return True

def objects_are_equal(a: object, b: object) -> bool:
    """
    Recursively checks if two objects are equal by value.

    This method supports objects that are compositions of:
        * built-in types (int, float, bool, etc)
        * callable objects
        * numpy arrays
        * objects supporting `__dict__`
        * compositions of the above objects

    Other types are currently unsupported.

    :param a: a in a == b, must implement __dict__ or be directly comparable.
    :param b: b in a == b, must implement __dict__ or be directly comparable.
    :return: true if both objects are the same, otherwise false.
    """
    if not hasattr(a, '__dict__') and (not hasattr(b, '__dict__')):
        return a == b
    a_dict = a.__dict__
    b_dict = b.__dict__
    if set(a_dict.keys()) != set(b_dict.keys()):
        return False
    for key in a_dict:
        if type(a_dict[key]) != type(b_dict[key]):
            return False
        if callable(a_dict[key]):
            if not callable_name_matches(a_dict[key], b_dict[key]):
                return False
        elif hasattr(a_dict[key], '__dict__'):
            if not objects_are_equal(a_dict[key], b_dict[key]):
                return False
        elif isinstance(a_dict[key], np.ndarray):
            if not np.allclose(a_dict[key], b_dict[key]):
                return False
        elif hasattr(a_dict[key], '__iter__'):
            if not iterator_is_equal(a_dict[key], b_dict[key]):
                return False
        else:
            return objects_are_equal(a_dict[key], b_dict[key])
    return True

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

def _build_model(self) -> LaneGCN:
    """
        Creates a new instance of a LaneGCN with some default parameters.
        """
    model = LaneGCN(map_net_scales=4, num_res_blocks=4, num_attention_layers=5, a2a_dist_threshold=20, l2a_dist_threshold=20, num_output_features=12, feature_dim=32, vector_map_feature_radius=30, vector_map_connection_scales=[1, 2, 3, 4], past_trajectory_sampling=TrajectorySampling(num_poses=4, time_horizon=1.5), future_trajectory_sampling=TrajectorySampling(num_poses=12, time_horizon=6))
    return model

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

def cache_scenarios_internal(args: List[Dict[str, Union[List[AbstractScenario], DictConfig]]]) -> List[CacheResult]:
    node_id = int(os.environ.get('NODE_RANK', 0))
    thread_id = str(uuid.uuid4())
    scenarios: List[AbstractScenario] = [a['scenario'] for a in args]
    cfg: DictConfig = args[0]['cfg']
    model = build_torch_module_wrapper(cfg.model)
    feature_builders = model.get_list_of_required_feature()
    target_builders = model.get_list_of_computed_target()
    del model
    assert cfg.cache.cache_path is not None, f'Cache path cannot be None when caching, got {cfg.cache.cache_path}'
    preprocessor = FeaturePreprocessor(cache_path=cfg.cache.cache_path, force_feature_computation=cfg.cache.force_feature_computation, feature_builders=feature_builders, target_builders=target_builders)
    logger.info('Extracted %s scenarios for thread_id=%s, node_id=%s.', str(len(scenarios)), thread_id, node_id)
    num_failures = 0
    num_successes = 0
    all_file_cache_metadata: List[Optional[CacheMetadataEntry]] = []
    for idx, scenario in enumerate(scenarios):
        logger.info('Processing scenario %s / %s in thread_id=%s, node_id=%s', idx + 1, len(scenarios), thread_id, node_id)
        features, targets, file_cache_metadata = preprocessor.compute_features(scenario)
        scenario_num_failures = sum((0 if feature.is_valid else 1 for feature in itertools.chain(features.values(), targets.values())))
        scenario_num_successes = len(features.values()) + len(targets.values()) - scenario_num_failures
        num_failures += scenario_num_failures
        num_successes += scenario_num_successes
        all_file_cache_metadata += file_cache_metadata
    logger.info('Finished processing scenarios for thread_id=%s, node_id=%s', thread_id, node_id)
    return [CacheResult(failures=num_failures, successes=num_successes, cache_metadata=all_file_cache_metadata)]

def build_training_engine(cfg: DictConfig, worker: WorkerPool) -> TrainingEngine:
    """
    Build the three core lightning modules: LightningDataModule, LightningModule and Trainer
    :param cfg: omegaconf dictionary
    :param worker: Worker to submit tasks which can be executed in parallel
    :return: TrainingEngine
    """
    logger.info('Building training engine...')
    torch_module_wrapper = build_torch_module_wrapper(cfg.model)
    datamodule = build_lightning_datamodule(cfg, worker, torch_module_wrapper)
    if cfg.lightning.trainer.params.accelerator == 'ddp':
        cfg = scale_cfg_for_distributed_training(cfg, datamodule=datamodule, worker=worker)
    else:
        logger.info(f'Updating configs based on {cfg.lightning.trainer.params.accelerator} strategy is currently not supported. Optimizer and LR Scheduler configs will not be updated.')
    model = build_lightning_module(cfg, torch_module_wrapper)
    trainer = build_trainer(cfg)
    engine = TrainingEngine(trainer=trainer, datamodule=datamodule, model=model)
    return engine

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

def create_dataset(samples: List[AbstractScenario], feature_preprocessor: FeaturePreprocessor, dataset_fraction: float, dataset_name: str, augmentors: Optional[List[AbstractAugmentor]]=None) -> torch.utils.data.Dataset:
    """
    Create a dataset from a list of samples.
    :param samples: List of dataset candidate samples.
    :param feature_preprocessor: Feature preprocessor object.
    :param dataset_fraction: Fraction of the dataset to load.
    :param dataset_name: Set name (train/val/test).
    :param scenario_type_loss_weights: Dictionary of scenario type loss weights.
    :param augmentors: List of augmentor objects for providing data augmentation to data samples.
    :return: The instantiated torch dataset.
    """
    num_keep = int(len(samples) * dataset_fraction)
    selected_scenarios = random.sample(samples, num_keep)
    logger.info(f'Number of samples in {dataset_name} set: {len(selected_scenarios)}')
    return ScenarioDataset(scenarios=selected_scenarios, feature_preprocessor=feature_preprocessor, augmentors=augmentors)

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

class ValidateSetupCallback(pl.Callback):
    """Validate that all features are computed that are requested by a model."""

    def on_before_accelerator_backend_setup(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """
        Called before the accelerator is being setup.
        Validate that datamodule and model do compute the same set of features, otherwise assert.
        :param trainer: Lightning trainer.
        :param pl_module: lightning model.
        """
        assert isinstance(pl_module, LightningModuleWrapper), 'pl_module is not LightningModuleWrapper!'
        assert hasattr(trainer, 'datamodule'), 'Trainer has no datamodule!'
        datamodule = trainer.datamodule
        assert isinstance(datamodule, DataModule), 'datamodule is not DataModule!'
        model_in_feature = pl_module.model.get_list_of_required_feature()
        datamodule_feature_types = datamodule.feature_and_targets_builder.get_list_of_feature_types()
        if len(model_in_feature) != len(datamodule_feature_types):
            logger.error('Length of model input feature and builder features is not the same!')
            for model_feature in pl_module.model.get_list_of_required_feature():
                logger.error(f'Model features: {model_feature}')
            for model_feature in datamodule.feature_and_targets_builder.get_list_of_feature_types():
                logger.error(f'Datamodel features: {model_feature}')
            raise RuntimeError('Not valid model setup!')
        for feature in model_in_feature:
            assert feature in datamodule_feature_types, f'Model input feature {feature} is not in builder!'
        model_out_feature = pl_module.model.get_list_of_computed_target()
        datamodule_target_types = datamodule.feature_and_targets_builder.get_list_of_target_types()
        assert len(model_out_feature) == len(datamodule_target_types), 'Length of model output feature and builder features is not the same!'
        for feature in model_out_feature:
            assert feature in datamodule_target_types, f'Model input feature {feature} is not in builder!'

def on_before_accelerator_backend_setup(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
    """
        Called before the accelerator is being setup.
        Validate that datamodule and model do compute the same set of features, otherwise assert.
        :param trainer: Lightning trainer.
        :param pl_module: lightning model.
        """
    assert isinstance(pl_module, LightningModuleWrapper), 'pl_module is not LightningModuleWrapper!'
    assert hasattr(trainer, 'datamodule'), 'Trainer has no datamodule!'
    datamodule = trainer.datamodule
    assert isinstance(datamodule, DataModule), 'datamodule is not DataModule!'
    model_in_feature = pl_module.model.get_list_of_required_feature()
    datamodule_feature_types = datamodule.feature_and_targets_builder.get_list_of_feature_types()
    if len(model_in_feature) != len(datamodule_feature_types):
        logger.error('Length of model input feature and builder features is not the same!')
        for model_feature in pl_module.model.get_list_of_required_feature():
            logger.error(f'Model features: {model_feature}')
        for model_feature in datamodule.feature_and_targets_builder.get_list_of_feature_types():
            logger.error(f'Datamodel features: {model_feature}')
        raise RuntimeError('Not valid model setup!')
    for feature in model_in_feature:
        assert feature in datamodule_feature_types, f'Model input feature {feature} is not in builder!'
    model_out_feature = pl_module.model.get_list_of_computed_target()
    datamodule_target_types = datamodule.feature_and_targets_builder.get_list_of_target_types()
    assert len(model_out_feature) == len(datamodule_target_types), 'Length of model output feature and builder features is not the same!'
    for feature in model_out_feature:
        assert feature in datamodule_target_types, f'Model input feature {feature} is not in builder!'

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

class TestCollateDataLoader(unittest.TestCase):
    """
    Tests data loading functionality
    """

    def setUp(self) -> None:
        """Set up the test case."""
        self.batch_size = 4
        feature_preprocessor = FeaturePreprocessor(cache_path=None, feature_builders=[RasterFeatureBuilder(map_features={'LANE': 1.0, 'INTERSECTION': 1.0, 'STOP_LINE': 0.5, 'CROSSWALK': 0.5}, num_input_channels=4, target_width=224, target_height=224, target_pixel_size=0.5, ego_width=2.297, ego_front_length=4.049, ego_rear_length=1.127, ego_longitudinal_offset=0.0, baseline_path_thickness=1), VectorMapFeatureBuilder(radius=20)], target_builders=[EgoTrajectoryTargetBuilder(TrajectorySampling(time_horizon=6.0, num_poses=12))], force_feature_computation=False)
        scenario = get_test_nuplan_scenario()
        scenarios = [scenario] * 3
        dataset = ScenarioDataset(scenarios=scenarios, feature_preprocessor=feature_preprocessor)
        self.dataloader = torch.utils.data.DataLoader(dataset=dataset, batch_size=self.batch_size, num_workers=2, pin_memory=False, drop_last=True, collate_fn=FeatureCollate())

    def test_dataloader(self) -> None:
        """
        Tests that the training dataloader can be iterated without errors
        """
        dataloader = self.dataloader
        dataloader_iter = iter(dataloader)
        iterations = min(len(dataloader), NUM_BATCHES)
        for _ in range(iterations):
            features, targets, scenarios = next(dataloader_iter)
            self.assertTrue('vector_map' in features.keys())
            vector_map: VectorMap = features['vector_map']
            self.assertEqual(vector_map.num_of_batches, self.batch_size)
            self.assertEqual(len(vector_map.coords), self.batch_size)
            self.assertEqual(len(vector_map.multi_scale_connections), self.batch_size)

def setUp(self) -> None:
    """Set up the test case."""
    self.batch_size = 4
    feature_preprocessor = FeaturePreprocessor(cache_path=None, feature_builders=[RasterFeatureBuilder(map_features={'LANE': 1.0, 'INTERSECTION': 1.0, 'STOP_LINE': 0.5, 'CROSSWALK': 0.5}, num_input_channels=4, target_width=224, target_height=224, target_pixel_size=0.5, ego_width=2.297, ego_front_length=4.049, ego_rear_length=1.127, ego_longitudinal_offset=0.0, baseline_path_thickness=1), VectorMapFeatureBuilder(radius=20)], target_builders=[EgoTrajectoryTargetBuilder(TrajectorySampling(time_horizon=6.0, num_poses=12))], force_feature_computation=False)
    scenario = get_test_nuplan_scenario()
    scenarios = [scenario] * 3
    dataset = ScenarioDataset(scenarios=scenarios, feature_preprocessor=feature_preprocessor)
    self.dataloader = torch.utils.data.DataLoader(dataset=dataset, batch_size=self.batch_size, num_workers=2, pin_memory=False, drop_last=True, collate_fn=FeatureCollate())

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

class TestVectorMapFeatureBuilder(unittest.TestCase):
    """Test feature builder that constructs map features in vectorized format."""

    def setUp(self) -> None:
        """
        Initializes DB
        """
        self.scenario = get_test_nuplan_scenario()

    def test_vector_map_feature_builder(self) -> None:
        """
        Test VectorMapFeatureBuilder
        """
        feature_builder = VectorMapFeatureBuilder(radius=20, connection_scales=[2])
        self.assertEqual(feature_builder.get_feature_type(), VectorMap)
        features = feature_builder.get_features_from_scenario(self.scenario)
        self.assertEqual(type(features), VectorMap)
        ego_state = self.scenario.initial_ego_state
        detections = self.scenario.initial_tracked_objects
        meta_data = PlannerInitialization(map_api=self.scenario.map_api, mission_goal=self.scenario.get_mission_goal(), route_roadblock_ids=self.scenario.get_route_roadblock_ids())
        history = SimulationHistoryBuffer.initialize_from_list(1, [ego_state], [detections], self.scenario.database_interval)
        iteration = SimulationIteration(TimePoint(0), 0)
        tl_data = self.scenario.get_traffic_light_status_at_iteration(iteration.index)
        current_input = PlannerInput(iteration=iteration, history=history, traffic_light_data=tl_data)
        features_sim = feature_builder.get_features_from_simulation(current_input=current_input, initialization=meta_data)
        self.assertEqual(type(features_sim), VectorMap)
        self.assertTrue(np.allclose(features_sim.coords[0], features.coords[0], atol=0.0001))
        for connections, connections_simulation in zip(features_sim.multi_scale_connections[0].values(), features.multi_scale_connections[0].values()):
            self.assertTrue(np.allclose(connections, connections_simulation))
        for lane in range(len(features_sim.lane_groupings[0])):
            for lane_groupings, lane_groupings_simulation in zip(features_sim.lane_groupings[0][lane], features.lane_groupings[0][lane]):
                self.assertTrue(np.allclose(lane_groupings, lane_groupings_simulation))
        self.assertTrue(np.allclose(features_sim.on_route_status[0], features.on_route_status[0], atol=0.0001))
        self.assertTrue(np.allclose(features_sim.traffic_light_data[0], features.traffic_light_data[0]))

    def test_vector_map_feature_builder_scripts_properly(self) -> None:
        """
        Tests that the VectorMapFeatureBuilder can be scripted properly.
        """
        feature_builder = VectorMapFeatureBuilder(radius=20, connection_scales=[2])
        self.assertEqual(feature_builder.get_feature_type(), VectorMap)
        scripted_builder = torch.jit.script(feature_builder)
        self.assertIsNotNone(scripted_builder)
        config = scripted_builder.precomputed_feature_config()
        self.assertTrue('initial_ego_state' in config)
        self.assertTrue('neighbor_vector_map' in config)
        self.assertTrue('radius' in config['neighbor_vector_map'])
        self.assertEqual('20', config['neighbor_vector_map']['radius'])
        num_lane_segment = 5
        num_connections = 7
        tensor_data = {'lane_segment_coords': torch.rand((num_lane_segment, 2, 2), dtype=torch.float64), 'lane_segment_conns': torch.zeros((num_connections, 2), dtype=torch.int64), 'on_route_status': torch.zeros((num_lane_segment, 2), dtype=torch.float32), 'traffic_light_array': torch.zeros((num_lane_segment, 4), dtype=torch.float32), 'anchor_state': torch.zeros((3,), dtype=torch.float64)}
        list_tensor_data = {'lane_segment_groupings': [torch.zeros(size=(2,), dtype=torch.int64) for _ in range(num_lane_segment)]}
        list_list_tensor_data: Dict[str, List[List[torch.Tensor]]] = {}
        scripted_tensor_output, scripted_list_output, scripted_list_list_output = scripted_builder.scriptable_forward(tensor_data, list_tensor_data, list_list_tensor_data)
        py_tensor_output, py_list_output, py_list_list_output = feature_builder.scriptable_forward(tensor_data, list_tensor_data, list_list_tensor_data)
        self.assertEqual(0, len(scripted_tensor_output))
        self.assertEqual(0, len(py_tensor_output))
        self.assertEqual(len(scripted_list_output), len(py_list_output))
        for key in py_list_output:
            self.assertEqual(len(py_list_output[key]), len(scripted_list_output[key]))
            for i in range(len(py_list_output[key])):
                torch.testing.assert_close(py_list_output[key][i], scripted_list_output[key][i])
        self.assertEqual(len(py_list_list_output), len(scripted_list_list_output))
        for key in py_list_list_output:
            py_list = py_list_list_output[key]
            scripted_list = scripted_list_list_output[key]
            self.assertEqual(len(py_list), len(scripted_list))
            for i in range(len(py_list)):
                py = py_list[i]
                script = scripted_list[i]
                self.assertEqual(len(py), len(script))
                for j in range(len(py)):
                    torch.testing.assert_close(py[j], script[j])

def setUp(self) -> None:
    """
        Initializes DB
        """
    self.scenario = get_test_nuplan_scenario()

class TestGenericAgentsFeatureBuilder(unittest.TestCase):
    """Test builder that constructs agent features during training and simulation."""

    def setUp(self) -> None:
        """
        Set up test case.
        """
        self.batch_size = 1
        self.past_time_horizon = 4.0
        self.num_agents = 10
        self.num_past_poses = 4
        self.num_total_past_poses = self.num_past_poses + 1
        self.agent_features = ['VEHICLE', 'PEDESTRIAN', 'BICYCLE', 'TRAFFIC_CONE', 'BARRIER', 'CZONE_SIGN', 'GENERIC_OBJECT']
        self.tracked_object_types: List[TrackedObjectType] = []
        for feature_name in self.agent_features:
            try:
                self.tracked_object_types.append(TrackedObjectType[feature_name])
            except KeyError:
                raise ValueError(f'Object representation for layer: {feature_name} is unavailable!')
        self.feature_builder = GenericAgentsFeatureBuilder(self.agent_features, TrajectorySampling(num_poses=self.num_past_poses, time_horizon=self.past_time_horizon))

    def test_generic_agent_feature_builder(self) -> None:
        """
        Test GenericAgentFeatureBuilder
        """
        scenario = MockAbstractScenario(number_of_past_iterations=10, number_of_detections=self.num_agents, tracked_object_types=self.tracked_object_types)
        feature = self.feature_builder.get_features_from_scenario(scenario)
        self.assertEqual(type(feature), GenericAgents)
        self.assertEqual(feature.batch_size, self.batch_size)
        self.assertEqual(len(feature.ego), self.batch_size)
        self.assertEqual(len(feature.ego[0]), self.num_total_past_poses)
        self.assertEqual(len(feature.ego[0][0]), GenericAgents.ego_state_dim())
        for feature_name in self.agent_features:
            self.assertTrue(feature_name in feature.agents)
            self.assertEqual(len(feature.agents[feature_name]), self.batch_size)
            self.assertEqual(len(feature.agents[feature_name][0]), self.num_total_past_poses)
            self.assertEqual(len(feature.agents[feature_name][0][0]), self.num_agents)
            self.assertEqual(len(feature.agents[feature_name][0][0][0]), GenericAgents.agents_states_dim())

    def test_no_agents(self) -> None:
        """
        Test when there are no agents
        """
        scenario = MockAbstractScenario(number_of_past_iterations=10, number_of_detections=0, tracked_object_types=self.tracked_object_types)
        feature = self.feature_builder.get_features_from_scenario(scenario)
        self.assertEqual(type(feature), GenericAgents)
        self.assertEqual(feature.batch_size, self.batch_size)
        self.assertEqual(len(feature.ego), self.batch_size)
        self.assertEqual(len(feature.ego[0]), self.num_total_past_poses)
        self.assertEqual(len(feature.ego[0][0]), GenericAgents.ego_state_dim())
        for feature_name in self.agent_features:
            self.assertTrue(feature_name in feature.agents)
            self.assertEqual(len(feature.agents[feature_name]), self.batch_size)
            self.assertEqual(len(feature.agents[feature_name][0]), self.num_total_past_poses)
            self.assertEqual(len(feature.agents[feature_name][0][0]), 0)
            self.assertEqual(feature.agents[feature_name][0].shape[1], 0)
            self.assertEqual(feature.agents[feature_name][0].shape[2], GenericAgents.agents_states_dim())

    def test_get_feature_from_simulation(self) -> None:
        """
        Test get feature from simulation
        """
        scenario = MockAbstractScenario(number_of_past_iterations=10, number_of_detections=self.num_agents, tracked_object_types=self.tracked_object_types)
        mock_meta_data = PlannerInitialization(map_api=MockAbstractMap(), route_roadblock_ids=None, mission_goal=StateSE2(0, 0, 0))
        ego_past_states = list(scenario.get_ego_past_trajectory(iteration=0, num_samples=10, time_horizon=5))
        ego_initial_state = scenario.initial_ego_state
        ego_history = ego_past_states + [ego_initial_state]
        past_observations = list(scenario.get_past_tracked_objects(iteration=0, num_samples=10, time_horizon=5))
        initial_observation = scenario.initial_tracked_objects
        observation_history = past_observations + [initial_observation]
        history = SimulationHistoryBuffer.initialize_from_list(len(ego_history), ego_history, observation_history, scenario.database_interval)
        current_input = PlannerInput(iteration=SimulationIteration(index=0, time_point=scenario.start_time), history=history, traffic_light_data=scenario.get_traffic_light_status_at_iteration(0))
        feature = self.feature_builder.get_features_from_simulation(current_input=current_input, initialization=mock_meta_data)
        self.assertEqual(type(feature), GenericAgents)
        self.assertEqual(feature.batch_size, self.batch_size)
        self.assertEqual(len(feature.ego), self.batch_size)
        self.assertEqual(len(feature.ego[0]), self.num_total_past_poses)
        self.assertEqual(len(feature.ego[0][0]), GenericAgents.ego_state_dim())
        for feature_name in self.agent_features:
            self.assertTrue(feature_name in feature.agents)
            self.assertEqual(len(feature.agents[feature_name]), self.batch_size)
            self.assertEqual(len(feature.agents[feature_name][0]), self.num_total_past_poses)
            self.assertEqual(len(feature.agents[feature_name][0][0]), self.num_agents)
            self.assertEqual(len(feature.agents[feature_name][0][0][0]), GenericAgents.agents_states_dim())

    def test_agents_feature_builder_scripts_properly(self) -> None:
        """
        Tests that the Generic Agents Feature Builder scripts properly
        """
        config = self.feature_builder.precomputed_feature_config()
        for expected_key in ['past_ego_states', 'past_time_stamps']:
            self.assertTrue(expected_key in config)
            config_dict = config[expected_key]
            self.assertTrue(len(config_dict) == 3)
            self.assertEqual(0, int(config_dict['iteration']))
            self.assertEqual(self.num_past_poses, int(config_dict['num_samples']))
            self.assertEqual(self.past_time_horizon, int(float(config_dict['time_horizon'])))
        tracked_objects_config_dict = config['past_tracked_objects']
        self.assertTrue(len(tracked_objects_config_dict) == 4)
        self.assertEqual(0, int(tracked_objects_config_dict['iteration']))
        self.assertEqual(self.num_past_poses, int(tracked_objects_config_dict['num_samples']))
        self.assertEqual(self.past_time_horizon, int(float(tracked_objects_config_dict['time_horizon'])))
        self.assertTrue('agent_features' in tracked_objects_config_dict)
        self.assertEqual(','.join(self.agent_features), tracked_objects_config_dict['agent_features'])
        num_frames = 5
        num_agents = 3
        ego_dim = EgoInternalIndex.dim()
        agent_dim = AgentInternalIndex.dim()
        past_ego_states = torch.zeros((num_frames, ego_dim), dtype=torch.float32)
        past_timestamps = torch.tensor([i * 50 for i in range(num_frames)], dtype=torch.int64)
        past_tracked_objects = [torch.ones((num_agents, agent_dim), dtype=torch.float32) for _ in range(num_frames)]
        for i in range(num_frames):
            for j in range(num_agents):
                past_tracked_objects[i][j, :] *= j + 1
        tensor_data = {'past_ego_states': past_ego_states, 'past_time_stamps': past_timestamps}
        list_tensor_data = {f'past_tracked_objects.{feature_name}': past_tracked_objects for feature_name in self.agent_features}
        list_list_tensor_data: Dict[str, List[List[torch.Tensor]]] = {}
        scripted_builder = torch.jit.script(self.feature_builder)
        scripted_tensors, scripted_list_tensors, scripted_list_list_tensors = scripted_builder.scriptable_forward(copy.deepcopy(tensor_data), copy.deepcopy(list_tensor_data), copy.deepcopy(list_list_tensor_data))
        py_tensors, py_list_tensors, py_list_list_tensors = self.feature_builder.scriptable_forward(copy.deepcopy(tensor_data), copy.deepcopy(list_tensor_data), copy.deepcopy(list_list_tensor_data))
        self.assertEqual(0, len(scripted_tensors))
        self.assertEqual(0, len(py_tensors))
        self.assertEqual(len(scripted_list_tensors), len(py_list_tensors))
        for key in py_list_tensors:
            scripted_list = scripted_list_tensors[key]
            py_list = py_list_tensors[key]
            self.assertEqual(len(py_list), len(scripted_list))
            for i in range(len(py_list)):
                scripted = scripted_list[i]
                py = py_list[i]
                torch.testing.assert_allclose(py, scripted, atol=0.05, rtol=0.05)
        self.assertEqual(0, len(scripted_list_list_tensors))
        self.assertEqual(0, len(py_list_list_tensors))

def setUp(self) -> None:
    """
        Set up test case.
        """
    self.batch_size = 1
    self.past_time_horizon = 4.0
    self.num_agents = 10
    self.num_past_poses = 4
    self.num_total_past_poses = self.num_past_poses + 1
    self.agent_features = ['VEHICLE', 'PEDESTRIAN', 'BICYCLE', 'TRAFFIC_CONE', 'BARRIER', 'CZONE_SIGN', 'GENERIC_OBJECT']
    self.tracked_object_types: List[TrackedObjectType] = []
    for feature_name in self.agent_features:
        try:
            self.tracked_object_types.append(TrackedObjectType[feature_name])
        except KeyError:
            raise ValueError(f'Object representation for layer: {feature_name} is unavailable!')
    self.feature_builder = GenericAgentsFeatureBuilder(self.agent_features, TrajectorySampling(num_poses=self.num_past_poses, time_horizon=self.past_time_horizon))

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

def build_lightning_datamodule(cfg: DictConfig, worker: WorkerPool, model: TorchModuleWrapper) -> pl.LightningDataModule:
    """
    Build the lightning datamodule from the config.
    :param cfg: Omegaconf dictionary.
    :param model: NN model used for training.
    :param worker: Worker to submit tasks which can be executed in parallel.
    :return: Instantiated datamodule object.
    """
    feature_builders = model.get_list_of_required_feature()
    target_builders = model.get_list_of_computed_target()
    splitter = build_splitter(cfg.splitter)
    feature_preprocessor = FeaturePreprocessor(cache_path=cfg.cache.cache_path, force_feature_computation=cfg.cache.force_feature_computation, feature_builders=feature_builders, target_builders=target_builders)
    augmentors = build_agent_augmentor(cfg.data_augmentation) if 'data_augmentation' in cfg else None
    scenarios = build_scenarios(cfg, worker, model)
    datamodule: pl.LightningDataModule = DataModule(feature_preprocessor=feature_preprocessor, splitter=splitter, all_scenarios=scenarios, dataloader_params=cfg.data_loader.params, augmentors=augmentors, worker=worker, scenario_type_sampling_weights=cfg.scenario_type_weights.scenario_type_sampling_weights, **cfg.data_loader.datamodule)
    return datamodule

def extract_scenarios_from_cache(cfg: DictConfig, worker: WorkerPool, model: TorchModuleWrapper) -> List[AbstractScenario]:
    """
    Build the scenario objects that comprise the training dataset from cache.
    :param cfg: Omegaconf dictionary.
    :param worker: Worker to submit tasks which can be executed in parallel.
    :param model: NN model used for training.
    :return: List of extracted scenarios.
    """
    cache_path = str(cfg.cache.cache_path)
    feature_builders = model.get_list_of_required_feature()
    target_builders = model.get_list_of_computed_target()
    feature_names = {builder.get_feature_unique_name() for builder in feature_builders + target_builders}
    scenario_cache_paths = get_s3_scenario_cache(cache_path, feature_names, worker) if cache_path.startswith('s3://') else get_local_scenario_cache(cache_path, feature_names)

    def filter_scenario_cache_paths_by_scenario_type(paths: List[Path]) -> List[Path]:
        """
        Filter the scenario cache paths by scenario type.
        :param paths: Scenario cache paths
        :return: Scenario cache paths filtered by desired scenario types
        """
        scenario_types_to_include = cfg.scenario_filter.scenario_types
        filtered_scenario_cache_paths = [path for path in paths if path.parent.name in scenario_types_to_include]
        return filtered_scenario_cache_paths
    if cfg.scenario_filter.scenario_types:
        validate_scenario_type_in_cache_path(scenario_cache_paths)
        logger.info('Filtering by desired scenario types')
        scenario_cache_paths = worker_map(worker, filter_scenario_cache_paths_by_scenario_type, scenario_cache_paths)
        assert len(scenario_cache_paths) > 0, f'Zero scenario cache paths after filtering by desired scenario types: {cfg.scenario_filter.scenario_types}. Please check if the cache contains the desired scenario type.'
    scenarios = worker_map(worker, create_scenario_from_paths, scenario_cache_paths)
    return cast(List[AbstractScenario], scenarios)

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

