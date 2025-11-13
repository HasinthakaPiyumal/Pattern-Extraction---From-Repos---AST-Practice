# Cluster 113

def _ego_starts_lane_change(initial_lane: Optional[Set[GraphEdgeMapObject]], start_timestamp: int) -> Optional[LaneChangeStartRecord]:
    """
    Opens lane change window and stores the information
    :param initial_lane: Set of common/connected route objects of corners of ego at previous timestamp
    :param start_timestamp: The current timestamp
    :return information on starts of a lane change if exists, otherwise None.
    """
    return LaneChangeStartRecord(start_timestamp, initial_lane) if initial_lane else None

