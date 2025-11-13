# Cluster 75

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

def test_simple_vector_net_model(self) -> None:
    """Test Model Vector Map Simple"""
    self.run_test_ml_planner(construct_simple_vector_map_ml_planner())

def test_raster_net_model(self) -> None:
    """Test Raster Net model"""
    self.run_test_ml_planner(construct_raster_ml_planner())

def test_urban_driver_open_loop_model(self) -> None:
    """Test UrbanDriverOpenLoop model"""
    self.run_test_ml_planner(construct_urban_driver_open_loop_ml_planner())

