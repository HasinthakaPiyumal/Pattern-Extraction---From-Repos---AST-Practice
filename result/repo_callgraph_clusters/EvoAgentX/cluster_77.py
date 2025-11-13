# Cluster 77

@contextmanager
def timeout(seconds: float):
    with TimeoutContext(seconds):
        yield

