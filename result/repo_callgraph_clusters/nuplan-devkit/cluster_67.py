# Cluster 67

def to_scene_goal_from_state(state: StateSE2) -> GoalScene:
    """
    Convert car footprint to scene structure for ego.
    :param car_footprint: CarFootprint of ego.
    :return Ego in scene format.
    """
    return GoalScene(pose=state)

