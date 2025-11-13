# Cluster 98

@dataclass
class SimulationFigure:
    """Simulation figure data."""
    planner_name: str
    scenario: AbstractScenario
    simulation_history: SimulationHistory
    vehicle_parameters: VehicleParameters
    figure: Figure
    file_path_index: int
    slider: Slider
    video_button: Button
    first_button: Button
    prev_button: Button
    play_button: Button
    next_button: Button
    last_button: Button
    figure_title_name: str
    x_y_coordinate_title: Title
    time_us: Optional[List[int]] = None
    mission_goal_plot: Optional[GlyphRenderer] = None
    expert_trajectory_plot: Optional[GlyphRenderer] = None
    legend_state: bool = False
    map_polygon_plots: Dict[str, GlyphRenderer] = field(default_factory=dict)
    map_line_plots: Dict[str, GlyphRenderer] = field(default_factory=dict)
    traffic_light_plot: Optional[TrafficLightPlot] = None
    ego_state_plot: Optional[EgoStatePlot] = None
    ego_state_trajectory_plot: Optional[EgoStateTrajectoryPlot] = None
    agent_state_plot: Optional[AgentStatePlot] = None
    agent_state_heading_plot: Optional[AgentStateHeadingPlot] = None
    lane_connectors: Optional[Dict[str, LaneConnector]] = None
    glyph_names_from_checkbox_group: Optional[Dict[str, str]] = None

    def __post_init__(self) -> None:
        """Initialize all plots and data sources."""
        if self.lane_connectors is None:
            self.lane_connectors = {}
        if self.time_us is None:
            self.time_us = []
        if self.traffic_light_plot is None:
            self.traffic_light_plot = TrafficLightPlot()
        if self.ego_state_plot is None:
            self.ego_state_plot = EgoStatePlot(vehicle_parameters=self.vehicle_parameters)
        if self.ego_state_trajectory_plot is None:
            self.ego_state_trajectory_plot = EgoStateTrajectoryPlot()
        if self.agent_state_plot is None:
            self.agent_state_plot = AgentStatePlot()
        if self.agent_state_heading_plot is None:
            self.agent_state_heading_plot = AgentStateHeadingPlot()

    def is_rendering(self) -> bool:
        """:return: true if at least one plot is currently rendering a frame request."""
        plots = [self.traffic_light_plot, self.ego_state_plot, self.ego_state_trajectory_plot, self.agent_state_plot, self.agent_state_heading_plot]
        return any((plot.render_event.is_set() if plot.render_event else False for plot in plots if plot))

    def figure_title_name_with_timestamp(self, frame_index: int) -> str:
        """
        Return figure title with a timestamp.
        :param frame_index: Frame index.
        """
        if self.time_us:
            return f'{self.figure_title_name} (Frame: {frame_index}, Time_us: {self.time_us[frame_index]})'
        else:
            return self.figure_title_name

    def copy_datasources(self, other: SimulationFigure) -> None:
        """
        Copy data sources from another simulation figure.
        :param other: Another SimulationFigure object.
        """
        self.time_us = other.time_us
        self.scenario = other.scenario
        self.simulation_history = other.simulation_history
        self.lane_connectors = other.lane_connectors
        self.traffic_light_plot.data_sources = other.traffic_light_plot.data_sources
        self.ego_state_plot.data_sources = other.ego_state_plot.data_sources
        self.ego_state_trajectory_plot.data_sources = other.ego_state_trajectory_plot.data_sources
        self.agent_state_plot.data_sources = other.agent_state_plot.data_sources
        self.agent_state_heading_plot.data_sources = other.agent_state_heading_plot.data_sources

    def update_data_sources(self) -> None:
        """
        Update data sources in a multi-threading manner to speed up loading and initialization in
        scenario rendering.
        """
        if len(self.simulation_history.data) == 0:
            raise ValueError('SimulationHistory cannot be empty!')
        self.slider.end = len(self.simulation_history.data) - 1
        self.time_us = [sample.ego_state.time_us for sample in self.simulation_history.data]
        for plot in [self.ego_state_plot, self.ego_state_trajectory_plot, self.agent_state_plot, self.agent_state_heading_plot]:
            if plot:
                t = threading.Thread(target=plot.update_data_sources, args=(self.simulation_history,), daemon=True)
                t.start()

    def update_map_dependent_data_sources(self) -> None:
        """
        Update data sources in a multi-threading manner to speed up loading and initialization in
        scenario rendering.
        """
        if len(self.simulation_history.data) == 0:
            raise ValueError('SimulationHistory cannot be empty!')
        if self.lane_connectors is not None and len(self.lane_connectors):
            if not self.traffic_light_plot:
                return
            thread = threading.Thread(target=self.traffic_light_plot.update_data_sources, args=(self.scenario, self.simulation_history, self.lane_connectors), daemon=True)
            thread.start()

    def render_mission_goal(self, mission_goal_state: StateSE2) -> None:
        """
        Render the mission goal.
        :param mission_goal_state: Mission goal state.
        """
        source = ColumnDataSource(dict(xs=[mission_goal_state.x], ys=[mission_goal_state.y], heading=[mission_goal_state.heading]))
        self.mission_goal_plot = self.figure.rect(x='xs', y='ys', height=self.vehicle_parameters.height, width=self.vehicle_parameters.length, angle='heading', fill_alpha=simulation_tile_style['mission_goal_alpha'], color=simulation_tile_style['mission_goal_color'], line_width=simulation_tile_style['mission_goal_line_width'], source=source)

    def render_expert_trajectory(self, expert_ego_trajectory_state: ColumnDataSource) -> None:
        """
        Render expert trajectory.
        :param expert_ego_trajectory_state: A list of trajectory states.
        """
        self.expert_trajectory_plot = self.figure.line(x='xs', y='ys', line_color=simulation_tile_trajectory_style['expert_ego']['line_color'], line_alpha=simulation_tile_trajectory_style['expert_ego']['line_alpha'], line_width=simulation_tile_trajectory_style['expert_ego']['line_width'], source=expert_ego_trajectory_state)

    @staticmethod
    def _update_glyph_visibility(glyphs: List[Optional[GlyphRenderer]]) -> None:
        """
        Update visibility in a list of glyphs.
        :param glyphs: A list of glyphs.
        """
        for glyph in glyphs:
            if glyph is not None:
                glyph.visible = not glyph.visible

    def get_glyph_name_from_checkbox_group(self, glyph_checkbox_group_name: str) -> str:
        """
        Get the correct glyph name of each glyph type based on the name from checkbox group.
        :param glyph_checkbox_group_name: glyph name from a checkbox group.
        :return Correct glyph name based on the glyph name from checkbox groups.
        """
        if not self.glyph_names_from_checkbox_group:
            self.glyph_names_from_checkbox_group = {'Vehicle': 'vehicles', 'Pedestrian': 'pedestrians', 'Bicycle': 'bicycles', 'Generic': 'genericobjects', 'Traffic Cone': 'traffic_cone', 'Barrier': 'barrier', 'Czone Sign': 'czone_sign', 'Lane': SemanticMapLayer.LANE.name, 'Intersection': SemanticMapLayer.INTERSECTION.name, 'Stop Line': SemanticMapLayer.STOP_LINE.name, 'Crosswalk': SemanticMapLayer.CROSSWALK.name, 'Walkway': SemanticMapLayer.WALKWAYS.name, 'Carpark': SemanticMapLayer.CARPARK_AREA.name, 'RoadBlock': SemanticMapLayer.ROADBLOCK.name, 'Lane Connector': SemanticMapLayer.LANE_CONNECTOR.name, 'Lane Line': SemanticMapLayer.LANE.name}
        name = self.glyph_names_from_checkbox_group.get(glyph_checkbox_group_name, None)
        if not name:
            raise ValueError(f'{glyph_checkbox_group_name} is not a valid glyph name!')
        return name

    def _get_trajectory_glyph_to_update(self, glyph_name: str) -> List[Optional[GlyphRenderer]]:
        """
        Get a trajectory glyph to update its visibility.
        :param glyph_name: Glyph name.
        :return A list of glyphs to be updated.
        """
        if glyph_name == 'Expert Trajectory':
            return [self.expert_trajectory_plot if self.expert_trajectory_plot is not None else None]
        elif glyph_name == 'Ego Trajectory':
            return [self.ego_state_trajectory_plot.plot if self.ego_state_trajectory_plot is not None else None]
        elif glyph_name == 'Goal':
            return [self.mission_goal_plot]
        elif glyph_name == 'Traffic Light':
            return [self.traffic_light_plot.plot if self.traffic_light_plot is not None else None]
        else:
            raise ValueError(f'{glyph_name} is not a valid trajectory name.')

    def _get_agent_glyph_to_update(self, glyph_name: str) -> List[Optional[GlyphRenderer]]:
        """
        Update an agent glyph to update its visibility.
        :param glyph_name: Glyph name.
        :return A list of glyphs to be updated.
        """
        object_type_name = self.get_glyph_name_from_checkbox_group(glyph_checkbox_group_name=glyph_name)
        return [self.agent_state_plot.plots.get(object_type_name, None) if self.agent_state_plot is not None else None, self.agent_state_heading_plot.plots.get(object_type_name, None) if self.agent_state_heading_plot is not None else None]

    def update_glyphs_visibility(self, glyph_names: Optional[List[str]]=None) -> None:
        """
        Update glyphs' visibility based on a list of glyph names.
        :param glyph_names: List of glyph names to update their visibility.
        """
        if not glyph_names:
            return
        glyphs = []
        for glyph_name in glyph_names:
            if glyph_name == 'Ego':
                glyphs += [self.ego_state_plot.plot if self.ego_state_plot is not None else None]
            elif glyph_name in ['Expert Trajectory', 'Ego Trajectory', 'Goal', 'Traffic Light']:
                glyphs += self._get_trajectory_glyph_to_update(glyph_name=glyph_name)
            elif glyph_name in ['Vehicle', 'Pedestrian', 'Bicycle', 'Generic', 'Traffic Cone', 'Barrier', 'Czone Sign']:
                glyphs += self._get_agent_glyph_to_update(glyph_name=glyph_name)
            elif glyph_name in ['Lane', 'Intersection', 'Stop Line', 'Crosswalk', 'Walkway', 'Carpark', 'RoadBlock']:
                map_polygon_name = self.get_glyph_name_from_checkbox_group(glyph_checkbox_group_name=glyph_name)
                glyphs += [self.map_polygon_plots.get(map_polygon_name, None)]
            elif glyph_name in ['Lane Connector', 'Lane Line']:
                map_line_name = self.get_glyph_name_from_checkbox_group(glyph_checkbox_group_name=glyph_name)
                glyphs += [self.map_line_plots.get(map_line_name, None)]
        self._update_glyph_visibility(glyphs=glyphs)

    def update_legend(self) -> None:
        """Update legend."""
        if self.legend_state:
            return
        if not self.agent_state_heading_plot or not self.agent_state_plot:
            return
        agent_legends = [(category.capitalize(), [plot, self.agent_state_heading_plot.plots[category]]) for category, plot in self.agent_state_plot.plots.items()]
        selected_map_polygon_layers = [SemanticMapLayer.LANE.name, SemanticMapLayer.INTERSECTION.name, SemanticMapLayer.STOP_LINE.name, SemanticMapLayer.CROSSWALK.name, SemanticMapLayer.WALKWAYS.name, SemanticMapLayer.CARPARK_AREA.name]
        map_polygon_legend_items = []
        for map_polygon_layer in selected_map_polygon_layers:
            map_polygon_legend_items.append((map_polygon_layer.capitalize(), [self.map_polygon_plots[map_polygon_layer]]))
        selected_map_line_layers = [SemanticMapLayer.LANE.name, SemanticMapLayer.LANE_CONNECTOR.name]
        map_line_legend_items = []
        for map_line_layer in selected_map_line_layers:
            map_line_legend_items.append((map_line_layer.capitalize(), [self.map_line_plots[map_line_layer]]))
        if not self.ego_state_plot or not self.ego_state_trajectory_plot:
            return
        legend_items = [('Ego', [self.ego_state_plot.plot]), ('Ego traj', [self.ego_state_trajectory_plot.plot])]
        if self.mission_goal_plot is not None:
            legend_items.append(('Goal', [self.mission_goal_plot]))
        if self.expert_trajectory_plot is not None:
            legend_items.append(('Expert traj', [self.expert_trajectory_plot]))
        legend_items += agent_legends
        legend_items += map_polygon_legend_items
        legend_items += map_line_legend_items
        if self.traffic_light_plot and self.traffic_light_plot.plot is not None:
            legend_items.append(('Traffic light', [self.traffic_light_plot.plot]))
        legend = Legend(items=legend_items)
        legend.click_policy = 'hide'
        self.figure.add_layout(legend)
        self.legend_state = True
        self.figure.legend.label_text_font_size = '0.8em'

def __post_init__(self) -> None:
    """Initialize all plots and data sources."""
    if self.lane_connectors is None:
        self.lane_connectors = {}
    if self.time_us is None:
        self.time_us = []
    if self.traffic_light_plot is None:
        self.traffic_light_plot = TrafficLightPlot()
    if self.ego_state_plot is None:
        self.ego_state_plot = EgoStatePlot(vehicle_parameters=self.vehicle_parameters)
    if self.ego_state_trajectory_plot is None:
        self.ego_state_trajectory_plot = EgoStateTrajectoryPlot()
    if self.agent_state_plot is None:
        self.agent_state_plot = AgentStatePlot()
    if self.agent_state_heading_plot is None:
        self.agent_state_heading_plot = AgentStateHeadingPlot()

