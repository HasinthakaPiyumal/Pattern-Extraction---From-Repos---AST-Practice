# Cluster 14

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

def test_scenario_visualization_utils(self) -> None:
    """Test if scenario visualization utils work as expected."""
    visualize_nuplan_scenarios(data_root=NUPLAN_DATA_ROOT, db_files=NUPLAN_DB_FILES, map_root=NUPLAN_MAPS_ROOT, map_version=NUPLAN_MAP_VERSION)

