# Cluster 30

def default_parallel() -> Parallel:
    """Returns a :class:`joblib.Parallel` instance with ``n_jobs`` equal to
    the number of CPUs on the host machine.
    """
    return Parallel(n_jobs=os.cpu_count(), prefer='processes', backend='loky')

