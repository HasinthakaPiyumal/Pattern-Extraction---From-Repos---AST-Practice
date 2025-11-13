# Cluster 105

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

def test_first_frame_button(self) -> None:
    """Tests that go to first frame button works correctly."""
    self._test_frame_index_request_button(button_name='first_button', frame_index_request=FrameIndexRequest.FIRST)

def test_last_frame_button(self) -> None:
    """Tests that go to last frame button works correctly."""
    self._test_frame_index_request_button(button_name='last_button', frame_index_request=FrameIndexRequest.LAST)

def test_prev_button(self) -> None:
    """Tests that show prev frame button works correctly."""
    self._test_frame_index_request_button(button_name='prev_button', frame_index_request=FrameIndexRequest.PREV)

def test_next_button(self) -> None:
    """Tests that show next frame button works correctly."""
    self._test_frame_index_request_button(button_name='next_button', frame_index_request=FrameIndexRequest.NEXT)

