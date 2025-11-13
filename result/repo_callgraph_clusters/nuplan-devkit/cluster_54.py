# Cluster 54

def get_test_nuplan_db_wrapper_nocache() -> NuPlanDBWrapper:
    """
    Gets a nuPlan DB wrapper object with default settings to be used in testing.
    This object will not be cached.
    """
    return NuPlanDBWrapper(data_root=NUPLAN_DATA_ROOT, map_root=NUPLAN_MAPS_ROOT, db_files=NUPLAN_DB_FILES, map_version=NUPLAN_MAP_VERSION)

