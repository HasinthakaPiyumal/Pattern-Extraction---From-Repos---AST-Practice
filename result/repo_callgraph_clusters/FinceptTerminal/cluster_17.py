# Cluster 17

def operation(msg):

    class MockOperation:

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass
    return MockOperation()

