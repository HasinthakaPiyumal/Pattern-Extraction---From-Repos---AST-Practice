# Cluster 116

def filter_scenarios_by_timestamp(scenario_dict: ScenarioDict, timestamp_threshold_s: float=5.0) -> ScenarioDict:
    """
    Filter the scenarios in a scenario dictionary by timestamp. Scenarios that occur are within `timestamp_threshold` of a particular scenario will be removed.
    This is only to be used during caching or during simulation. This currently cannot be used during training as `CachedScenario` does not implement timestamp information.
    :param scenario_dict: Dictionary that holds a list of scenarios for each scenario type.
    :param timestamp_threshold_s: Threshold for filtering out scenarios clustered together in time.
    :return: Filtered scenario dictinoary.
    """
    for scenario_type in scenario_dict:
        scenario_dict[scenario_type] = _filter_scenarios_by_timestamp(scenario_dict[scenario_type], timestamp_threshold_s)
    return scenario_dict

