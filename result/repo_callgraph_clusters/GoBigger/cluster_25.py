# Cluster 25

def create_collision_detection(cd_type, **cd_kwargs):
    if cd_type == 'exhaustive':
        return ExhaustiveCollisionDetection(**cd_kwargs)
    if cd_type == 'precision':
        return PrecisionCollisionDetection(**cd_kwargs)
    if cd_type == 'rebuild_quadtree':
        return RebuildQuadTreeCollisionDetection(**cd_kwargs)
    if cd_type == 'remove_quadtree':
        return RemoveQuadTreeCollisionDetection(**cd_kwargs)
    else:
        raise NotImplementedError

