# Cluster 111

class EgoLatJerkStatistics(WithinBoundMetricBase):
    """Ego lateral jerk metric."""

    def __init__(self, name: str, category: str) -> None:
        """
        Initializes the EgoLatJerkStatistics class
        :param name: Metric name
        :param category: Metric category.
        """
        super().__init__(name=name, category=category)

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the lateral jerk  metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated lateral jerk metric.
        """
        metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_cubed', extract_function=extract_ego_jerk, extract_function_params={'acceleration_coordinate': 'y'})
        return metric_statistics

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Returns the lateral jerk  metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated lateral jerk metric.
        """
    metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_cubed', extract_function=extract_ego_jerk, extract_function_params={'acceleration_coordinate': 'y'})
    return metric_statistics

class EgoAccelerationStatistics(WithinBoundMetricBase):
    """Ego acceleration metric."""

    def __init__(self, name: str, category: str) -> None:
        """
        Initializes the EgoAccelerationStatistics class
        :param name: Metric name
        :param category: Metric category.
        """
        super().__init__(name=name, category=category)

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the estimated metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated metric.
        """
        metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_squared', extract_function=extract_ego_acceleration, extract_function_params={'acceleration_coordinate': 'magnitude'})
        return metric_statistics

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Returns the estimated metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated metric.
        """
    metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_squared', extract_function=extract_ego_acceleration, extract_function_params={'acceleration_coordinate': 'magnitude'})
    return metric_statistics

class EgoJerkStatistics(WithinBoundMetricBase):
    """Ego jerk metric."""

    def __init__(self, name: str, category: str, max_abs_mag_jerk: float) -> None:
        """
        Initializes the EgoProgressAlongExpertRouteStatistics class
        :param name: Metric name
        :param category: Metric category
        :param max_abs_mag_jerk: Maximum threshold to define if absolute jerk is within bound.
        """
        super().__init__(name=name, category=category)
        self._max_abs_mag_jerk = max_abs_mag_jerk

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the jerk metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated jerk metric.
        """
        metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_cubed', extract_function=extract_ego_jerk, extract_function_params={'acceleration_coordinate': 'magnitude'}, min_within_bound_threshold=-self._max_abs_mag_jerk, max_within_bound_threshold=self._max_abs_mag_jerk)
        return metric_statistics

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Returns the jerk metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated jerk metric.
        """
    metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_cubed', extract_function=extract_ego_jerk, extract_function_params={'acceleration_coordinate': 'magnitude'}, min_within_bound_threshold=-self._max_abs_mag_jerk, max_within_bound_threshold=self._max_abs_mag_jerk)
    return metric_statistics

class EgoLatAccelerationStatistics(WithinBoundMetricBase):
    """Ego lateral acceleration metric."""

    def __init__(self, name: str, category: str, max_abs_lat_accel: float) -> None:
        """
        Initializes the EgoLatAccelerationStatistics class
        :param name: Metric name
        :param category: Metric category
        :param max_abs_lat_accel: Maximum threshold to define if absolute lateral acceleration is within bound.
        """
        super().__init__(name=name, category=category)
        self._max_abs_lat_accel = max_abs_lat_accel

    @staticmethod
    def compute_comfortability(history: SimulationHistory, max_abs_lat_accel: float) -> bool:
        """
        Compute comfortability based on max_abs_lat_accel
        :param history: History from a simulation engine
        :param max_abs_lat_accel: Threshold for the absolute lat jerk
        :return True if within the threshold otherwise false.
        """
        ego_pose_states = history.extract_ego_state
        ego_pose_lat_accels = extract_ego_acceleration(ego_pose_states, acceleration_coordinate='y')
        lat_accels_within_bounds = np.abs(ego_pose_lat_accels) < max_abs_lat_accel
        return bool(np.all(lat_accels_within_bounds))

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the lateral acceleration metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated lateral acceleration metric.
        """
        metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_squared', extract_function=extract_ego_acceleration, extract_function_params={'acceleration_coordinate': 'y'}, min_within_bound_threshold=-self._max_abs_lat_accel, max_within_bound_threshold=self._max_abs_lat_accel)
        return metric_statistics

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Returns the lateral acceleration metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated lateral acceleration metric.
        """
    metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_squared', extract_function=extract_ego_acceleration, extract_function_params={'acceleration_coordinate': 'y'}, min_within_bound_threshold=-self._max_abs_lat_accel, max_within_bound_threshold=self._max_abs_lat_accel)
    return metric_statistics

class EgoLonAccelerationStatistics(WithinBoundMetricBase):
    """Ego longitudinal acceleration metric."""

    def __init__(self, name: str, category: str, min_lon_accel: float, max_lon_accel: float) -> None:
        """
        Initializes the EgoLonAccelerationStatistics class
        :param name: Metric name
        :param category: Metric category
        :param min_lon_accel: Threshold to define if the lon acceleration is within bound
        :param max_lon_accel: Threshold to define if the lat acceleration is within bound.
        """
        super().__init__(name=name, category=category)
        self._min_lon_accel = min_lon_accel
        self._max_lon_accel = max_lon_accel

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the longitudinal acceleration metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated longitudinal acceleration metric.
        """
        metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_squared', extract_function=extract_ego_acceleration, extract_function_params={'acceleration_coordinate': 'x'}, min_within_bound_threshold=self._min_lon_accel, max_within_bound_threshold=self._max_lon_accel)
        return metric_statistics

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Returns the longitudinal acceleration metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated longitudinal acceleration metric.
        """
    metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_squared', extract_function=extract_ego_acceleration, extract_function_params={'acceleration_coordinate': 'x'}, min_within_bound_threshold=self._min_lon_accel, max_within_bound_threshold=self._max_lon_accel)
    return metric_statistics

class EgoYawAccelerationStatistics(WithinBoundMetricBase):
    """Ego yaw acceleration metric."""

    def __init__(self, name: str, category: str, max_abs_yaw_accel: float) -> None:
        """
        Initializes the EgoYawAccelerationStatistics class
        :param name: Metric name
        :param category: Metric category
        :param max_abs_yaw_accel: Maximum threshold to define if absolute yaw acceleration is within bound.
        """
        super().__init__(name=name, category=category)
        self._max_abs_yaw_accel = max_abs_yaw_accel

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the yaw acceleration metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated yaw acceleration metric.
        """
        metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='radians_per_second_squared', extract_function=extract_ego_yaw_rate, extract_function_params={'deriv_order': 2, 'poly_order': 3}, min_within_bound_threshold=-self._max_abs_yaw_accel, max_within_bound_threshold=self._max_abs_yaw_accel)
        return metric_statistics

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Returns the yaw acceleration metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated yaw acceleration metric.
        """
    metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='radians_per_second_squared', extract_function=extract_ego_yaw_rate, extract_function_params={'deriv_order': 2, 'poly_order': 3}, min_within_bound_threshold=-self._max_abs_yaw_accel, max_within_bound_threshold=self._max_abs_yaw_accel)
    return metric_statistics

class EgoYawRateStatistics(WithinBoundMetricBase):
    """Ego yaw rate metric."""

    def __init__(self, name: str, category: str, max_abs_yaw_rate: float) -> None:
        """
        Initializes the EgoYawRateStatistics class
        :param name: Metric name
        :param category: Metric category
        :param max_abs_yaw_rate: Maximum threshold to define if absolute yaw rate is within bound.
        """
        super().__init__(name=name, category=category)
        self._max_abs_yaw_rate = max_abs_yaw_rate

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the yaw rate  metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated yaw rate metric.
        """
        metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='radians_per_second', extract_function=extract_ego_yaw_rate, extract_function_params={}, min_within_bound_threshold=-self._max_abs_yaw_rate, max_within_bound_threshold=self._max_abs_yaw_rate)
        return metric_statistics

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Returns the yaw rate  metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated yaw rate metric.
        """
    metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='radians_per_second', extract_function=extract_ego_yaw_rate, extract_function_params={}, min_within_bound_threshold=-self._max_abs_yaw_rate, max_within_bound_threshold=self._max_abs_yaw_rate)
    return metric_statistics

class EgoLonJerkStatistics(WithinBoundMetricBase):
    """Ego longitudinal jerk metric."""

    def __init__(self, name: str, category: str, max_abs_lon_jerk: float) -> None:
        """
        Initializes the EgoLonJerkStatistics class
        :param name: Metric name
        :param category: Metric category
        :param max_abs_lon_jerk: Maximum threshold to define if lon jerk is within bound.
        """
        super().__init__(name=name, category=category)
        self._max_abs_lon_jerk = max_abs_lon_jerk

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the longitudinal jerk metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated longitudinal jerk metric.
        """
        metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_cubed', extract_function=extract_ego_jerk, extract_function_params={'acceleration_coordinate': 'x'}, min_within_bound_threshold=-self._max_abs_lon_jerk, max_within_bound_threshold=self._max_abs_lon_jerk)
        return metric_statistics

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Returns the longitudinal jerk metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated longitudinal jerk metric.
        """
    metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_cubed', extract_function=extract_ego_jerk, extract_function_params={'acceleration_coordinate': 'x'}, min_within_bound_threshold=-self._max_abs_lon_jerk, max_within_bound_threshold=self._max_abs_lon_jerk)
    return metric_statistics

