# Cluster 104

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

def update_decorations() -> None:
    main_figure.figure.title.text = main_figure.figure_title_name_with_timestamp(frame_index=frame_index)
    main_figure.update_glyphs_visibility(glyph_names=hidden_glyph_names)

class ScenarioTab(BaseTab):
    """Scenario tab in nuboard."""

    def __init__(self, doc: Document, experiment_file_data: ExperimentFileData, vehicle_parameters: VehicleParameters, scenario_builder: AbstractScenarioBuilder, async_rendering: bool=True, frame_rate_cap_hz: int=60):
        """
        Scenario tab to render metric results about a scenario.
        :param doc: Bokeh HTML document.
        :param experiment_file_data: Experiment file data.
        :param vehicle_parameters: Vehicle parameters.
        :param scenario_builder: nuPlan scenario builder instance.
        :param async_rendering: When true, will use threads to render SimulationTiles asynchronously.
        :param frame_rate_cap_hz: Maximum frames to render per second. Internally this value is capped at 60.
        """
        super().__init__(doc=doc, experiment_file_data=experiment_file_data)
        self._number_metrics_per_figure: int = 4
        self.planner_checkbox_group.name = 'scenario_planner_checkbox_group'
        self._scenario_builder = scenario_builder
        self._scenario_title_div = Div(**ScenarioTabTitleDivConfig.get_config())
        self._scalar_scenario_type_select = Select(name='scenario_scalar_scenario_type_select', css_classes=['scalar-scenario-type-select'])
        self._scalar_scenario_type_select.on_change('value', self._scalar_scenario_type_select_on_change)
        self._scalar_log_name_select = Select(name='scenario_scalar_log_name_select', css_classes=['scalar-log-name-select'])
        self._scalar_log_name_select.on_change('value', self._scalar_log_name_select_on_change)
        self._scalar_scenario_name_select = Select(name='scenario_scalar_name_select', css_classes=['scalar-scenario-name-select'])
        self._scalar_scenario_name_select.js_on_change('value', ScenarioTabUpdateWindowsSizeJSCode.get_js_code())
        self._scalar_scenario_name_select.on_change('value', self._scalar_scenario_name_select_on_change)
        self._scenario_token_multi_choice = MultiChoice(**ScenarioTabScenarioTokenMultiChoiceConfig.get_config())
        self._scenario_token_multi_choice.on_change('value', self._scenario_token_multi_choice_on_change)
        self._scenario_modal_query_btn = Button(**ScenarioTabModalQueryButtonConfig.get_config())
        self._scenario_modal_query_btn.js_on_click(ScenarioTabLoadingJSCode.get_js_code())
        self._scenario_modal_query_btn.on_click(self._scenario_modal_query_button_on_click)
        self.planner_checkbox_group.js_on_change('active', ScenarioTabLoadingJSCode.get_js_code())
        self._default_time_series_div = Div(text=' <p> No time series results, please add more experiments or\n                adjust the search filter.</p>', css_classes=['scenario-default-div'], margin=default_div_style['margin'], width=default_div_style['width'])
        self._time_series_layout = column(self._default_time_series_div, css_classes=['scenario-time-series-layout'], name='time_series_layout')
        self._default_ego_expert_states_div = Div(text=' <p> No expert and ego states, please add more experiments or\n                        adjust the search filter.</p>', css_classes=['scenario-default-div'], margin=default_div_style['margin'], width=default_div_style['width'])
        self._ego_expert_states_layout = column(self._default_ego_expert_states_div, css_classes=['scenario-ego-expert-states-layout'], name='ego_expert_states_layout')
        self._default_simulation_div = Div(text=' <p> No simulation data, please add more experiments or\n                adjust the search filter.</p>', css_classes=['scenario-default-div'], margin=default_div_style['margin'], width=default_div_style['width'])
        self._simulation_tile_layout = column(self._default_simulation_div, css_classes=['scenario-simulation-layout'], name='simulation_tile_layout')
        self._simulation_tile_layout.js_on_change('children', ScenarioTabLoadingEndJSCode.get_js_code())
        self.simulation_tile = SimulationTile(map_factory=self._scenario_builder.get_map_factory(), doc=self._doc, vehicle_parameters=vehicle_parameters, experiment_file_data=experiment_file_data, async_rendering=async_rendering, frame_rate_cap_hz=frame_rate_cap_hz)
        self._default_scenario_score_div = Div(text=' <p> No scenario score results, please add more experiments or\n                        adjust the search filter.</p>', css_classes=['scenario-default-div'], margin=default_div_style['margin'], width=default_div_style['width'])
        self._scenario_score_layout = column(self._default_scenario_score_div, css_classes=['scenario-score-layout'], name='scenario_score_layout')
        self._scenario_metric_score_data_figure_sizes = scenario_tab_style['scenario_metric_score_figure_sizes']
        self._scenario_metric_score_data: scenario_metric_score_dict_type = {}
        self._time_series_data: Dict[str, List[ScenarioTimeSeriesData]] = {}
        self._simulation_figure_data: List[SimulationData] = []
        self._available_scenario_names: List[str] = []
        self._simulation_plots: Optional[column] = None
        object_types = ['Ego', 'Vehicle', 'Pedestrian', 'Bicycle', 'Generic', 'Traffic Cone', 'Barrier', 'Czone Sign']
        self._object_checkbox_group = CheckboxGroup(labels=object_types, active=list(range(len(object_types))), css_classes=['scenario-object-checkbox-group'], name='scenario_object_checkbox_group')
        self._object_checkbox_group.on_change('active', self._object_checkbox_group_active_on_change)
        trajectories = ['Expert Trajectory', 'Ego Trajectory', 'Goal', 'Traffic Light', 'RoadBlock']
        self._traj_checkbox_group = CheckboxGroup(labels=trajectories, active=list(range(len(trajectories))), css_classes=['scenario-traj-checkbox-group'], name='scenario_traj_checkbox_group')
        self._traj_checkbox_group.on_change('active', self._traj_checkbox_group_active_on_change)
        map_objects = ['Lane', 'Intersection', 'Stop Line', 'Crosswalk', 'Walkway', 'Carpark', 'Lane Connector', 'Lane Line']
        self._map_checkbox_group = CheckboxGroup(labels=map_objects, active=list(range(len(map_objects))), css_classes=['scenario-map-checkbox-group'], name='scenario_map_checkbox_group')
        self._map_checkbox_group.on_change('active', self._map_checkbox_group_active_on_change)
        self.plot_state_keys = ['x [m]', 'y [m]', 'heading [rad]', 'velocity_x [m/s]', 'velocity_y [m/s]', 'speed [m/s]', 'acceleration_x [m/s^2]', 'acceleration_y [m/s^2]', 'acceleration [m/s^2]', 'steering_angle [rad]', 'yaw_rate [rad/s]']
        self.expert_planner_key = 'Expert'
        self._init_selection()

    @property
    def scenario_title_div(self) -> Div:
        """Return scenario title div."""
        return self._scenario_title_div

    @property
    def scalar_scenario_type_select(self) -> Select:
        """Return scalar_scenario_type_select."""
        return self._scalar_scenario_type_select

    @property
    def scalar_log_name_select(self) -> Select:
        """Return scalar_log_name_select."""
        return self._scalar_log_name_select

    @property
    def scalar_scenario_name_select(self) -> Select:
        """Return scalar_scenario_name_select."""
        return self._scalar_scenario_name_select

    @property
    def scenario_token_multi_choice(self) -> MultiChoice:
        """Return scenario_token multi choice."""
        return self._scenario_token_multi_choice

    @property
    def scenario_modal_query_btn(self) -> Button:
        """Return scenario_modal_query_button."""
        return self._scenario_modal_query_btn

    @property
    def object_checkbox_group(self) -> CheckboxGroup:
        """Return object checkbox group."""
        return self._object_checkbox_group

    @property
    def traj_checkbox_group(self) -> CheckboxGroup:
        """Return traj checkbox group."""
        return self._traj_checkbox_group

    @property
    def map_checkbox_group(self) -> CheckboxGroup:
        """Return map checkbox group."""
        return self._map_checkbox_group

    @property
    def time_series_layout(self) -> column:
        """Return time_series_layout."""
        return self._time_series_layout

    @property
    def scenario_score_layout(self) -> column:
        """Return scenario_score_layout."""
        return self._scenario_score_layout

    @property
    def simulation_tile_layout(self) -> column:
        """Return simulation_tile_layout."""
        return self._simulation_tile_layout

    @property
    def ego_expert_states_layout(self) -> column:
        """Return time_series_state_layout."""
        return self._ego_expert_states_layout

    def _update_glyph_checkbox_group(self, glyph_names: List[str]) -> None:
        """
        Update visibility of glyphs according to checkbox group.
        :param glyph_names: A list of updated glyph names.
        """
        for simulation_figure in self.simulation_tile.figures:
            simulation_figure.update_glyphs_visibility(glyph_names=glyph_names)

    def _traj_checkbox_group_active_on_change(self, attr: str, old: List[int], new: List[int]) -> None:
        """
        Helper function for traj checkbox group when the list of actives changes.
        :param attr: Attribute name.
        :param old: Old active index.
        :param new: New active index.
        """
        active_indices = list(set(old) - set(new)) + list(set(new) - set(old))
        active_labels = [self._traj_checkbox_group.labels[index] for index in active_indices]
        self._update_glyph_checkbox_group(glyph_names=active_labels)

    def _map_checkbox_group_active_on_change(self, attr: str, old: List[int], new: List[int]) -> None:
        """
        Helper function for map checkbox group when the list of actives changes.
        :param attr: Attribute name.
        :param old: Old active index.
        :param new: New active index.
        """
        active_indices = list(set(old) - set(new)) + list(set(new) - set(old))
        active_labels = [self._map_checkbox_group.labels[index] for index in active_indices]
        self._update_glyph_checkbox_group(glyph_names=active_labels)

    def _object_checkbox_group_active_on_change(self, attr: str, old: List[int], new: List[int]) -> None:
        """
        Helper function for object checkbox group when the list of actives changes.
        :param attr: Attribute name.
        :param old: Old active index.
        :param new: New active index.
        """
        active_indices = list(set(old) - set(new)) + list(set(new) - set(old))
        active_labels = [self._object_checkbox_group.labels[index] for index in active_indices]
        self._update_glyph_checkbox_group(glyph_names=active_labels)

    def file_paths_on_change(self, experiment_file_data: ExperimentFileData, experiment_file_active_index: List[int]) -> None:
        """
        Interface to update layout when file_paths is changed.
        :param experiment_file_data: Experiment file data.
        :param experiment_file_active_index: Active indexes for experiment files.
        """
        self._experiment_file_data = experiment_file_data
        self._experiment_file_active_index = experiment_file_active_index
        self.simulation_tile.init_simulations(figure_sizes=self.simulation_figure_sizes)
        self._init_selection()
        self._scenario_metric_score_data = self._update_aggregation_metric()
        self._update_scenario_plot()

    def _click_planner_checkbox_group(self, attr: Any) -> None:
        """
        Click event handler for planner_checkbox_group.
        :param attr: Clicked attributes.
        """
        scenario_metric_score_figure_data = self._render_scenario_metric_score()
        scenario_metric_score_layout = self._render_scenario_metric_layout(figure_data=scenario_metric_score_figure_data, default_div=self._default_scenario_score_div, plot_width=self._scenario_metric_score_data_figure_sizes[0], legend=False)
        self._scenario_score_layout.children[0] = layout(scenario_metric_score_layout)
        filtered_time_series_data: Dict[str, List[ScenarioTimeSeriesData]] = defaultdict(list)
        for key, time_series_data in self._time_series_data.items():
            for data in time_series_data:
                if data.planner_name not in self.enable_planner_names:
                    continue
                filtered_time_series_data[key].append(data)
        time_series_figure_data = self._render_time_series(aggregated_time_series_data=filtered_time_series_data)
        time_series_figures = self._render_scenario_metric_layout(figure_data=time_series_figure_data, default_div=self._default_time_series_div, plot_width=self.plot_sizes[0], legend=True)
        self._time_series_layout.children[0] = layout(time_series_figures)
        filtered_simulation_figures = [data for data in self._simulation_figure_data if data.planner_name in self.enable_planner_names]
        if not filtered_simulation_figures:
            simulation_layouts = column(self._default_simulation_div)
            ego_expert_state_layouts = column(self._default_ego_expert_states_div)
        else:
            simulation_layouts = gridplot([simulation_figure.plot for simulation_figure in filtered_simulation_figures], ncols=self.get_plot_cols(plot_width=self.simulation_figure_sizes[0], offset_width=scenario_tab_style['col_offset_width']), toolbar_location=None)
            ego_expert_state_layouts = self._render_ego_expert_states(simulation_figure_data=filtered_simulation_figures)
        self._simulation_tile_layout.children[0] = layout(simulation_layouts)
        self._ego_expert_states_layout.children[0] = layout(ego_expert_state_layouts)

    def _update_simulation_layouts(self) -> None:
        """Update simulation layouts."""
        self._simulation_tile_layout.children[0] = layout(self._simulation_plots)

    def _update_scenario_plot(self) -> None:
        """Update scenario plots when selection is made."""
        start_time = time.perf_counter()
        self._simulation_figure_data = []
        scenario_metric_score_figure_data = self._render_scenario_metric_score()
        scenario_metric_score_layout = self._render_scenario_metric_layout(figure_data=scenario_metric_score_figure_data, default_div=self._default_scenario_score_div, plot_width=self._scenario_metric_score_data_figure_sizes[0], legend=False)
        self._scenario_score_layout.children[0] = layout(scenario_metric_score_layout)
        self._time_series_data = self._aggregate_time_series_data()
        time_series_figure_data = self._render_time_series(aggregated_time_series_data=self._time_series_data)
        time_series_figures = self._render_scenario_metric_layout(figure_data=time_series_figure_data, default_div=self._default_time_series_div, plot_width=self.plot_sizes[0], legend=True)
        self._time_series_layout.children[0] = layout(time_series_figures)
        self._simulation_plots = self._render_simulations()
        ego_expert_state_layout = self._render_ego_expert_states(simulation_figure_data=self._simulation_figure_data)
        self._ego_expert_states_layout.children[0] = layout(ego_expert_state_layout)
        self._doc.add_next_tick_callback(self._update_simulation_layouts)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        logger.info(f'Rending scenario plot takes {elapsed_time:.4f} seconds.')

    def _update_planner_names(self) -> None:
        """Update planner name options in the checkbox widget."""
        self.planner_checkbox_group.labels = []
        self.planner_checkbox_group.active = []
        selected_keys = [key for key in self.experiment_file_data.simulation_scenario_keys if key.scenario_type == self._scalar_scenario_type_select.value and key.scenario_name == self._scalar_scenario_name_select.value]
        sorted_planner_names = sorted(list({key.planner_name for key in selected_keys}))
        self.planner_checkbox_group.labels = sorted_planner_names
        self.planner_checkbox_group.active = [index for index in range(len(sorted_planner_names))]

    def _scalar_scenario_type_select_on_change(self, attr: str, old: str, new: str) -> None:
        """
        Helper function to change event in scalar scenario type.
        :param attr: Attribute.
        :param old: Old value.
        :param new: New value.
        """
        if new == '':
            return
        available_log_names = self.load_log_name(scenario_type=self._scalar_scenario_type_select.value)
        self._scalar_log_name_select.options = [''] + available_log_names
        self._scalar_log_name_select.value = ''
        self._scalar_scenario_name_select.options = ['']
        self._scalar_scenario_name_select.value = ''

    def _scalar_log_name_select_on_change(self, attr: str, old: str, new: str) -> None:
        """
        Helper function to change event in scalar log name.
        :param attr: Attribute.
        :param old: Old value.
        :param new: New value.
        """
        if new == '':
            return
        available_scenario_names = self.load_scenario_names(scenario_type=self._scalar_scenario_type_select.value, log_name=self._scalar_log_name_select.value)
        self._scalar_scenario_name_select.options = [''] + available_scenario_names
        self._scalar_scenario_name_select.value = ''

    def _scalar_scenario_name_select_on_change(self, attr: str, old: str, new: str) -> None:
        """
        Helper function to change event in scalar scenario name.
        :param attr: Attribute.
        :param old: Old value.
        :param new: New value.
        """
        if self._scalar_scenario_name_select.tags:
            self.window_width = self._scalar_scenario_name_select.tags[0]
            self.window_height = self._scalar_scenario_name_select.tags[1]

    def _scenario_token_multi_choice_on_change(self, attr: str, old: List[str], new: List[str]) -> None:
        """
        Helper function to change event in scenario token multi choice.
        :param attr: Attribute.
        :param old: List of old values.
        :param new: List of new values.
        """
        available_scenario_tokens = self._experiment_file_data.available_scenario_tokens
        if not available_scenario_tokens or not new:
            return
        scenario_token_info = available_scenario_tokens.get(new[0])
        if self._scalar_scenario_type_select.value != scenario_token_info.scenario_type:
            self._scalar_scenario_type_select.value = scenario_token_info.scenario_type
        if self._scalar_log_name_select.value != scenario_token_info.log_name:
            self._scalar_log_name_select.value = scenario_token_info.log_name
        if self._scalar_scenario_name_select.value != scenario_token_info.scenario_name:
            self.scalar_scenario_name_select.value = scenario_token_info.scenario_name

    def _scenario_modal_query_button_on_click(self) -> None:
        """Helper function when click the modal query button."""
        if self._scalar_scenario_name_select.tags:
            self.window_width = self._scalar_scenario_name_select.tags[0]
            self.window_height = self._scalar_scenario_name_select.tags[1]
        self._update_planner_names()
        self._update_scenario_plot()

    def _init_selection(self) -> None:
        """Init histogram and scalar selection options."""
        self._scalar_scenario_type_select.value = ''
        self._scalar_scenario_type_select.options = []
        self._scalar_log_name_select.value = ''
        self._scalar_log_name_select.options = []
        self._scalar_scenario_name_select.value = ''
        self._scalar_scenario_name_select.options = []
        self._available_scenario_names = []
        self._simulation_figure_data = []
        if len(self._scalar_scenario_type_select.options) == 0:
            self._scalar_scenario_type_select.options = [''] + self.experiment_file_data.available_scenario_types
        if len(self._scalar_scenario_type_select.options) > 0:
            self._scalar_scenario_type_select.value = self._scalar_scenario_type_select.options[0]
        available_scenario_tokens = list(self._experiment_file_data.available_scenario_tokens.keys())
        self._scenario_token_multi_choice.options = available_scenario_tokens
        self._update_planner_names()

    @staticmethod
    def _render_scalar_figure(title: str, y_axis_label: str, hover: HoverTool, sizes: List[int], x_axis_label: Optional[str]=None, x_range: Optional[List[str]]=None, y_range: Optional[List[str]]=None) -> Figure:
        """
        Render a scalar figure.
        :param title: Plot title.
        :param y_axis_label: Y axis label.
        :param hover: Hover tool for the plot.
        :param sizes: Width and height in pixels.
        :param x_axis_label: Label in x axis.
        :param x_range: Labels in x major axis.
        :param y_range: Labels in y major axis.
        :return A time series plot.
        """
        scenario_scalar_figure = Figure(background_fill_color=PLOT_PALETTE['background_white'], title=title, css_classes=['time-series-figure'], margin=scenario_tab_style['time_series_figure_margins'], width=sizes[0], height=sizes[1], active_scroll='wheel_zoom', output_backend='webgl', x_range=x_range, y_range=y_range)
        scenario_scalar_figure.add_tools(hover)
        scenario_scalar_figure.title.text_font_size = scenario_tab_style['time_series_figure_title_text_font_size']
        scenario_scalar_figure.xaxis.axis_label_text_font_size = scenario_tab_style['time_series_figure_xaxis_axis_label_text_font_size']
        scenario_scalar_figure.xaxis.major_label_text_font_size = scenario_tab_style['time_series_figure_xaxis_major_label_text_font_size']
        scenario_scalar_figure.yaxis.axis_label_text_font_size = scenario_tab_style['time_series_figure_yaxis_axis_label_text_font_size']
        scenario_scalar_figure.yaxis.major_label_text_font_size = scenario_tab_style['time_series_figure_yaxis_major_label_text_font_size']
        scenario_scalar_figure.toolbar.logo = None
        scenario_scalar_figure.xaxis.major_label_orientation = np.pi / 4
        scenario_scalar_figure.yaxis.axis_label = y_axis_label
        scenario_scalar_figure.xaxis.axis_label = x_axis_label
        return scenario_scalar_figure

    def _update_aggregation_metric(self) -> scenario_metric_score_dict_type:
        """
        Update metric score for each scenario.
        :return A dict of log name: {scenario names and their metric scores}.
        """
        data: scenario_metric_score_dict_type = defaultdict(lambda: defaultdict(list))
        for index, metric_aggregator_dataframes in enumerate(self.experiment_file_data.metric_aggregator_dataframes):
            if index not in self._experiment_file_active_index:
                continue
            for file_index, (metric_aggregator_filename, metric_aggregator_dataframe) in enumerate(metric_aggregator_dataframes.items()):
                columns = set(list(metric_aggregator_dataframe.columns))
                non_metric_columns = {'scenario', 'log_name', 'scenario_type', 'num_scenarios', 'planner_name', 'aggregator_type'}
                metric_columns = sorted(list(columns - non_metric_columns))
                for _, row_data in metric_aggregator_dataframe.iterrows():
                    num_scenarios = row_data['num_scenarios']
                    if not np.isnan(num_scenarios):
                        continue
                    planner_name = row_data['planner_name']
                    scenario_name = row_data['scenario']
                    log_name = row_data['log_name']
                    for metric_column in metric_columns:
                        score = row_data[metric_column]
                        if score is not None:
                            data[log_name][scenario_name].append(ScenarioMetricScoreData(experiment_index=index, metric_aggregator_file_name=metric_aggregator_filename, metric_aggregator_file_index=file_index, planner_name=planner_name, metric_statistic_name=metric_column, score=np.round(score, 4)))
        return data

    def _aggregate_time_series_data(self) -> Dict[str, List[ScenarioTimeSeriesData]]:
        """
        Aggregate time series data.
        :return A dict of metric statistic names and their data.
        """
        aggregated_time_series_data: Dict[str, List[ScenarioTimeSeriesData]] = {}
        scenario_types = tuple([self._scalar_scenario_type_select.value]) if self._scalar_scenario_type_select.value else None
        log_names = tuple([self._scalar_log_name_select.value]) if self._scalar_log_name_select.value else None
        if not len(self._scalar_scenario_name_select.value):
            return aggregated_time_series_data
        for index, metric_statistics_dataframes in enumerate(self.experiment_file_data.metric_statistics_dataframes):
            if index not in self._experiment_file_active_index:
                continue
            for metric_statistics_dataframe in metric_statistics_dataframes:
                planner_names = metric_statistics_dataframe.planner_names
                if metric_statistics_dataframe.metric_statistic_name not in aggregated_time_series_data:
                    aggregated_time_series_data[metric_statistics_dataframe.metric_statistic_name] = []
                for planner_name in planner_names:
                    data_frame = metric_statistics_dataframe.query_scenarios(scenario_names=tuple([str(self._scalar_scenario_name_select.value)]), scenario_types=scenario_types, planner_names=tuple([planner_name]), log_names=log_names)
                    if not len(data_frame):
                        continue
                    time_series_headers = metric_statistics_dataframe.time_series_headers
                    time_series: pandas.DataFrame = data_frame[time_series_headers]
                    if time_series[time_series_headers[0]].iloc[0] is None:
                        continue
                    time_series_values: npt.NDArray[np.float64] = np.round(np.asarray(list(chain.from_iterable(time_series[metric_statistics_dataframe.time_series_values_column]))), 4)
                    time_series_timestamps = list(chain.from_iterable(time_series[metric_statistics_dataframe.time_series_timestamp_column]))
                    time_series_unit = time_series[metric_statistics_dataframe.time_series_unit_column].iloc[0]
                    time_series_selected_frames = metric_statistics_dataframe.get_time_series_selected_frames
                    scenario_time_series_data = ScenarioTimeSeriesData(experiment_index=index, planner_name=planner_name, time_series_values=time_series_values, time_series_timestamps=time_series_timestamps, time_series_unit=time_series_unit, time_series_selected_frames=time_series_selected_frames)
                    aggregated_time_series_data[metric_statistics_dataframe.metric_statistic_name].append(scenario_time_series_data)
        return aggregated_time_series_data

    def _render_time_series(self, aggregated_time_series_data: Dict[str, List[ScenarioTimeSeriesData]]) -> Dict[str, Figure]:
        """
        Render time series plots.
        :param aggregated_time_series_data: Aggregated scenario time series data.
        :return A dict of figure name and figures.
        """
        time_series_figures: Dict[str, Figure] = {}
        for metric_statistic_name, scenario_time_series_data in aggregated_time_series_data.items():
            for data in scenario_time_series_data:
                if not len(data.time_series_values):
                    continue
                if metric_statistic_name not in time_series_figures:
                    time_series_figures[metric_statistic_name] = self._render_scalar_figure(title=metric_statistic_name, y_axis_label=data.time_series_unit, x_axis_label='frame', hover=HoverTool(tooltips=[('Frame', '@x'), ('Value', '@y{0.0000}'), ('Time_us', '@time_us'), ('Planner', '$name')]), sizes=self.plot_sizes)
                planner_name = data.planner_name + f' ({self.get_file_path_last_name(data.experiment_index)})'
                color = self.experiment_file_data.file_path_colors[data.experiment_index][data.planner_name]
                time_series_figure = time_series_figures[metric_statistic_name]
                timestamp_frames = data.time_series_selected_frames if data.time_series_selected_frames is not None else list(range(len(data.time_series_timestamps)))
                data_source = ColumnDataSource(dict(x=timestamp_frames, y=data.time_series_values, time_us=data.time_series_timestamps))
                if data.time_series_selected_frames is not None:
                    time_series_figure.scatter(x='x', y='y', name=planner_name, color=color, legend_label=planner_name, source=data_source)
                else:
                    time_series_figure.line(x='x', y='y', name=planner_name, color=color, legend_label=planner_name, source=data_source)
        return time_series_figures

    def _render_scenario_metric_score_scatter(self, scatter_figure: Figure, scenario_metric_score_data: Dict[str, List[ScenarioMetricScoreData]]) -> None:
        """
        Render scatter plot with scenario metric score data.
        :param scatter_figure: A scatter figure.
        :param scenario_metric_score_data: Metric score data for a scenario.
        """
        data_sources: Dict[str, ScenarioMetricScoreDataSource] = {}
        for metric_name, metric_score_data in scenario_metric_score_data.items():
            for index, score_data in enumerate(metric_score_data):
                experiment_name = self.get_file_path_last_name(score_data.experiment_index)
                legend_label = f'{score_data.planner_name} ({experiment_name})'
                data_source_index = legend_label + f' - {score_data.metric_aggregator_file_index})'
                if data_source_index not in data_sources:
                    data_sources[data_source_index] = ScenarioMetricScoreDataSource(xs=[], ys=[], planners=[], aggregators=[], experiments=[], fill_colors=[], marker=self.get_scatter_sign(score_data.metric_aggregator_file_index), legend_label=legend_label)
                fill_color = self.experiment_file_data.file_path_colors[score_data.experiment_index][score_data.planner_name]
                data_sources[data_source_index].xs.append(score_data.metric_statistic_name)
                data_sources[data_source_index].ys.append(score_data.score)
                data_sources[data_source_index].planners.append(score_data.planner_name)
                data_sources[data_source_index].aggregators.append(score_data.metric_aggregator_file_name)
                data_sources[data_source_index].experiments.append(self.get_file_path_last_name(score_data.experiment_index))
                data_sources[data_source_index].fill_colors.append(fill_color)
        for legend_label, data_source in data_sources.items():
            sources = ColumnDataSource(dict(xs=data_source.xs, ys=data_source.ys, planners=data_source.planners, experiments=data_source.experiments, aggregators=data_source.aggregators, fill_colors=data_source.fill_colors, line_colors=data_source.fill_colors))
            glyph_renderer = self.get_scatter_render_func(scatter_sign=data_source.marker, scatter_figure=scatter_figure)
            glyph_renderer(x='xs', y='ys', size=10, fill_color='fill_colors', line_color='fill_colors', source=sources)

    def _render_scenario_metric_score(self) -> Dict[str, Figure]:
        """
        Render scenario metric score plot.
        :return A dict of figure names and figures.
        """
        if not self._scalar_log_name_select.value or not self._scalar_scenario_name_select.value or (not self._scenario_metric_score_data):
            return {}
        selected_scenario_metric_score: List[ScenarioMetricScoreData] = self._scenario_metric_score_data[self._scalar_log_name_select.value][self._scalar_scenario_name_select.value]
        data: Dict[str, List[ScenarioMetricScoreData]] = defaultdict(list)
        for scenario_metric_score_data in selected_scenario_metric_score:
            if scenario_metric_score_data.planner_name not in self.enable_planner_names:
                continue
            metric_statistic_name = scenario_metric_score_data.metric_statistic_name
            data[metric_statistic_name].append(scenario_metric_score_data)
        metric_statistic_names = sorted(list(set(data.keys())))
        if 'score' in metric_statistic_names:
            metric_statistic_names.remove('score')
            metric_statistic_names.append('score')
        hover = HoverTool(tooltips=[('Metric', '@xs'), ('Score', '@ys'), ('Planner', '@planners'), ('Experiment', '@experiments'), ('Aggregator', '@aggregators')])
        number_of_figures = ceil(len(metric_statistic_names) / self._number_metrics_per_figure)
        scenario_metric_score_figures: Dict[str, Figure] = defaultdict()
        for index in range(number_of_figures):
            starting_index = index * self._number_metrics_per_figure
            ending_index = starting_index + self._number_metrics_per_figure
            selected_metric_names = metric_statistic_names[starting_index:ending_index]
            scenario_metric_score_figure = self._render_scalar_figure(title='', y_axis_label='score', hover=hover, x_range=selected_metric_names, sizes=self._scenario_metric_score_data_figure_sizes)
            metric_score_data = {metric_name: data[metric_name] for metric_name in selected_metric_names}
            self._render_scenario_metric_score_scatter(scatter_figure=scenario_metric_score_figure, scenario_metric_score_data=metric_score_data)
            scenario_metric_score_figures[str(index)] = scenario_metric_score_figure
        return scenario_metric_score_figures

    def _render_grid_plot(self, figures: Dict[str, Figure], plot_width: int, legend: bool=True) -> LayoutDOM:
        """
        Render a grid plot.
        :param figures: A dict of figure names and figures.
        :param plot_width: Width of each plot.
        :param legend: If figures have legends.
        :return A grid plot.
        """
        figure_plot_list: List[Figure] = []
        for figure_name, figure_plot in figures.items():
            if legend:
                figure_plot.legend.label_text_font_size = scenario_tab_style['plot_legend_label_text_font_size']
                figure_plot.legend.background_fill_alpha = 0.0
                figure_plot.legend.click_policy = 'hide'
            figure_plot_list.append(figure_plot)
        grid_plot = gridplot(figure_plot_list, ncols=self.get_plot_cols(plot_width=plot_width), toolbar_location='left')
        return grid_plot

    def _render_scenario_metric_layout(self, figure_data: Dict[str, Figure], default_div: Div, plot_width: int, legend: bool=True) -> column:
        """
        Render a layout for scenario metric.
        :param figure_data: A dict of figure_data.
        :param default_div: Default message when there is no result.
        :param plot_width: Figure width.
        :param legend: If figures have legends.
        :return A bokeh column layout.
        """
        if not figure_data:
            return column(default_div)
        grid_plot = self._render_grid_plot(figures=figure_data, plot_width=plot_width, legend=legend)
        scenario_metric_layout = column(grid_plot)
        return scenario_metric_layout

    def _render_simulations(self) -> column:
        """
        Render simulation plot.
        :return: A list of Bokeh columns or rows.
        """
        selected_keys = [key for key in self.experiment_file_data.simulation_scenario_keys if key.scenario_type == self._scalar_scenario_type_select.value and key.log_name == self._scalar_log_name_select.value and (key.scenario_name == self._scalar_scenario_name_select.value) and (key.nuboard_file_index in self._experiment_file_active_index)]
        if not selected_keys:
            self._scenario_title_div.text = '-'
            simulation_layouts = column(self._default_simulation_div)
        else:
            hidden_glyph_names = [label for checkbox_group in [self._object_checkbox_group, self._traj_checkbox_group, self._map_checkbox_group] for index, label in enumerate(checkbox_group.labels) if index not in checkbox_group.active]
            self._simulation_figure_data = self.simulation_tile.render_simulation_tiles(selected_scenario_keys=selected_keys, figure_sizes=self.simulation_figure_sizes, hidden_glyph_names=hidden_glyph_names)
            simulation_figures = [data.plot for data in self._simulation_figure_data]
            simulation_layouts = gridplot(simulation_figures, ncols=self.get_plot_cols(plot_width=self.simulation_figure_sizes[0], offset_width=scenario_tab_style['col_offset_width']), toolbar_location=None)
            self._scenario_title_div.text = f'{self._scalar_scenario_type_select.value} - {self._scalar_log_name_select.value} - {self._scalar_scenario_name_select.value}'
        return simulation_layouts

    @staticmethod
    def _get_ego_expert_states(state_key: str, ego_state: EgoState) -> float:
        """
        Get states based on the state key.
        :param state_key: Ego state key.
        :param ego_state: Ego state.
        :return ego state based on the key.
        """
        if state_key == 'x [m]':
            return cast(float, ego_state.car_footprint.center.x)
        elif state_key == 'y [m]':
            return cast(float, ego_state.car_footprint.center.y)
        elif state_key == 'velocity_x [m/s]':
            return cast(float, ego_state.dynamic_car_state.rear_axle_velocity_2d.x)
        elif state_key == 'velocity_y [m/s]':
            return cast(float, ego_state.dynamic_car_state.rear_axle_velocity_2d.y)
        elif state_key == 'speed [m/s]':
            return cast(float, ego_state.dynamic_car_state.speed)
        elif state_key == 'acceleration_x [m/s^2]':
            return cast(float, ego_state.dynamic_car_state.rear_axle_acceleration_2d.x)
        elif state_key == 'acceleration_y [m/s^2]':
            return cast(float, ego_state.dynamic_car_state.rear_axle_acceleration_2d.y)
        elif state_key == 'acceleration [m/s^2]':
            return cast(float, ego_state.dynamic_car_state.acceleration)
        elif state_key == 'heading [rad]':
            return cast(float, ego_state.car_footprint.center.heading)
        elif state_key == 'steering_angle [rad]':
            return cast(float, ego_state.dynamic_car_state.tire_steering_rate)
        elif state_key == 'yaw_rate [rad/s]':
            return cast(float, ego_state.dynamic_car_state.angular_velocity)
        else:
            raise ValueError(f'{state_key} not available!')

    def _render_ego_expert_state_glyph(self, ego_expert_plot_aggregated_states: scenario_ego_expert_state_figure_type, ego_expert_plot_colors: Dict[str, str]) -> column:
        """
        Render line and circle glyphs on ego_expert_state figures and get a grid plot.
        :param ego_expert_plot_aggregated_states: Aggregated ego and expert states over frames.
        :param ego_expert_plot_colors: Colors for different planners.
        :return Column layout for ego and expert states.
        """
        ego_expert_state_figures: Dict[str, Figure] = defaultdict()
        for plot_state_key in self.plot_state_keys:
            hover = HoverTool(tooltips=[('Frame', '@x'), ('Value', '@y{0.0000}'), ('Planner', '$name')])
            ego_expert_state_figure = self._render_scalar_figure(title='', y_axis_label=plot_state_key, x_axis_label='frame', hover=hover, sizes=scenario_tab_style['ego_expert_state_figure_sizes'])
            ego_expert_state_figure.yaxis.formatter = BasicTickFormatter(use_scientific=False)
            ego_expert_state_figures[plot_state_key] = ego_expert_state_figure
        for planner_name, plot_states in ego_expert_plot_aggregated_states.items():
            color = ego_expert_plot_colors.get(planner_name, None)
            if not color:
                color = None
            for plot_state_key, plot_state_values in plot_states.items():
                ego_expert_state_figure = ego_expert_state_figures[plot_state_key]
                data_source = ColumnDataSource(dict(x=list(range(len(plot_state_values))), y=np.round(plot_state_values, 2)))
                if self.expert_planner_key in planner_name:
                    ego_expert_state_figure.circle(x='x', y='y', name=planner_name, color=color, legend_label=planner_name, source=data_source, size=2)
                else:
                    ego_expert_state_figure.line(x='x', y='y', name=planner_name, color=color, legend_label=planner_name, source=data_source, line_width=1)
        ego_expert_states_layout = self._render_grid_plot(figures=ego_expert_state_figures, plot_width=scenario_tab_style['ego_expert_state_figure_sizes'][0], legend=True)
        return ego_expert_states_layout

    def _get_ego_expert_plot_color(self, planner_name: str, file_path_index: int, figure_planer_name: str) -> str:
        """
        Get color for ego expert plot states based on the planner name.
        :param planner_name: Plot planner name.
        :param file_path_index: File path index for the plot.
        :param figure_planer_name: Figure original planner name.
        """
        return cast(str, self.experiment_file_data.expert_color_palettes[file_path_index] if self.expert_planner_key in planner_name else self.experiment_file_data.file_path_colors[file_path_index][figure_planer_name])

    def _render_ego_expert_states(self, simulation_figure_data: List[SimulationData]) -> column:
        """
        Render expert and ego time series states. Make sure it is called after _render_simulation.
        :param simulation_figure_data: Simulation figure data after rendering simulation.
        :return Column layout for ego and expert states.
        """
        if not simulation_figure_data:
            return column(self._default_ego_expert_states_div)
        ego_expert_plot_aggregated_states: scenario_ego_expert_state_figure_type = defaultdict(lambda: defaultdict(list))
        ego_expert_plot_colors: Dict[str, str] = defaultdict()
        for figure_data in simulation_figure_data:
            experiment_file_index = figure_data.simulation_figure.file_path_index
            experiment_name = self.get_file_path_last_name(experiment_file_index)
            expert_planner_name = f'{self.expert_planner_key} - ({experiment_name})'
            ego_planner_name = f'{figure_data.planner_name} - ({experiment_name})'
            ego_expert_states = {expert_planner_name: figure_data.simulation_figure.scenario.get_expert_ego_trajectory(), ego_planner_name: figure_data.simulation_figure.simulation_history.extract_ego_state}
            for planner_name, planner_states in ego_expert_states.items():
                ego_expert_plot_colors[planner_name] = self._get_ego_expert_plot_color(planner_name=planner_name, figure_planer_name=figure_data.planner_name, file_path_index=figure_data.simulation_figure.file_path_index)
                if planner_name in ego_expert_plot_aggregated_states:
                    continue
                for planner_state in planner_states:
                    for plot_state_key in self.plot_state_keys:
                        state_key_value = self._get_ego_expert_states(state_key=plot_state_key, ego_state=planner_state)
                        ego_expert_plot_aggregated_states[planner_name][plot_state_key].append(state_key_value)
        ego_expert_states_layout = self._render_ego_expert_state_glyph(ego_expert_plot_aggregated_states=ego_expert_plot_aggregated_states, ego_expert_plot_colors=ego_expert_plot_colors)
        return ego_expert_states_layout

def _update_glyph_checkbox_group(self, glyph_names: List[str]) -> None:
    """
        Update visibility of glyphs according to checkbox group.
        :param glyph_names: A list of updated glyph names.
        """
    for simulation_figure in self.simulation_tile.figures:
        simulation_figure.update_glyphs_visibility(glyph_names=glyph_names)

