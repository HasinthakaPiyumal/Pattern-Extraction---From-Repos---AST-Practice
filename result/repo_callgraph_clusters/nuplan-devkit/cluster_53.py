# Cluster 53

def generate_minimal_nuplan_db(parameters: DBGenerationParameters) -> None:
    """
    Generate a synthetic nuplan_db based on the supplied generation parameters.
    :param parameters: The parameters to use for generation.
    """
    mapping_keys = _generate_mapping_keys(parameters)
    _generate_lidar_pc_table(mapping_keys['lidar_pc'], parameters.file_path)
    _generate_lidar_table(mapping_keys['lidar'], parameters.file_path)
    _generate_image_table(mapping_keys['image'], parameters.file_path)
    _generate_camera_table(mapping_keys['camera'], parameters.file_path)
    _generate_ego_pose_table(mapping_keys['ego_pose'], parameters.file_path)
    _generate_scene_table(mapping_keys['scene'], parameters.file_path)
    _generate_traffic_light_status_table(mapping_keys['traffic_light_status'], parameters.file_path)
    _generate_lidar_box_table(mapping_keys['lidar_box'], parameters.file_path)
    _generate_track_table(mapping_keys['track'], parameters.file_path)
    _generate_scenario_tag_table(mapping_keys['scenario_tag'], parameters.file_path)
    _generate_category_table(parameters.file_path)
    _generate_log_table(parameters.file_path)

