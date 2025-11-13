# Cluster 96

def aggregate_metric_aggregator_dataframe_histogram_data(dataframe_file_name: str, metric_aggregator_dataframe: pd.DataFrame, metric_aggregator_dataframe_index: int, scenario_types: List[str]) -> List[HistogramData]:
    """
    Aggregate metric statistics dataframe data for histograms.
    :param dataframe_file_name: Dataframe file name.
    :param metric_aggregator_dataframe: Metric aggregator dataframe.
    :param metric_aggregator_dataframe_index: Metric aggregator dataframe index.
    :param scenario_types: List of selected scenario types.
    :return A dictionary of {aggregator planner_name: {aggregator scenario type: a list of (scenario type score,
    scenario log name)}}.
    """
    scenario_type_score_histogram_statistics_dict = _extract_metric_aggregator_scenario_type_score_data(metric_aggregator_dataframe=metric_aggregator_dataframe, scenario_types=scenario_types)
    histogram_data_list = extract_scenario_score_type_score_histogram_data(metric_aggregator_dataframe_index=metric_aggregator_dataframe_index, scenario_type_score_histogram_statistics_dict=scenario_type_score_histogram_statistics_dict, histogram_file_name=dataframe_file_name)
    return histogram_data_list

