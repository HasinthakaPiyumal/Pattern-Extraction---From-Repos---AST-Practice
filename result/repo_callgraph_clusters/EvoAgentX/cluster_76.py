# Cluster 76

class TimeoutContext:
    """
    A reliable cross-platform timeout context manager using stopit
    
    Usage:
        with TimeoutContext(seconds=5):
            # code that may timeout
            do_something()
    """

    def __init__(self, seconds: Union[int, float]):
        self.seconds = float(seconds)
        self._cm = None
        self._result = None

    def __enter__(self):
        self._cm = timeout_set_to(self.seconds)
        self._result = self._cm.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cm.__exit__(exc_type, exc_val, exc_tb)
        if self._result.triggered:
            raise TimeoutException('Operation timed out')
        return False

def __enter__(self):
    self._cm = timeout_set_to(self.seconds)
    self._result = self._cm.__enter__()
    return self

