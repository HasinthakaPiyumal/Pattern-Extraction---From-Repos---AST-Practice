# Cluster 59

def pytest_configure(config: Any) -> None:
    """Configures pytest"""
    config.addinivalue_line('markers', 'nuplan_test(type): mark test to run only on named environment')

