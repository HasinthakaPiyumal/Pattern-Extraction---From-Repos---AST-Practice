# Cluster 49

def is_ray_available() -> bool:
    try:
        try_to_import_ray()
        return True
    except ValueError:
        return False

