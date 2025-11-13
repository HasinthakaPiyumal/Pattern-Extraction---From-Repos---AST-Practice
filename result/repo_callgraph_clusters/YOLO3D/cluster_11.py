# Cluster 11

class Timeout(contextlib.ContextDecorator):

    def __init__(self, seconds, *, timeout_msg='', suppress_timeout_errors=True):
        self.seconds = int(seconds)
        self.timeout_message = timeout_msg
        self.suppress = bool(suppress_timeout_errors)

    def _timeout_handler(self, signum, frame):
        raise TimeoutError(self.timeout_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(self.seconds)

    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)
        if self.suppress and exc_type is TimeoutError:
            return True

def __enter__(self):
    signal.signal(signal.SIGALRM, self._timeout_handler)
    signal.alarm(self.seconds)

def __exit__(self, exc_type, exc_val, exc_tb):
    signal.alarm(0)
    if self.suppress and exc_type is TimeoutError:
        return True

