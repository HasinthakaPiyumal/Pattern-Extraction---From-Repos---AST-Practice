# Cluster 112

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

def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> Optional[float]:
    """Inherited, see superclass.
        The total score for this metric is defined as the product of the scores for VRUs, vehicles and object track types. If no at fault collision exist, the score is 1.
        """
    return 1 if metric_statistics[0].value else self._compute_collision_score(metric_statistics[2].value, self._max_violation_threshold_vru) * self._compute_collision_score(metric_statistics[3].value, self._max_violation_threshold_vehicle) * self._compute_collision_score(metric_statistics[4].value, self._max_violation_threshold_object)

