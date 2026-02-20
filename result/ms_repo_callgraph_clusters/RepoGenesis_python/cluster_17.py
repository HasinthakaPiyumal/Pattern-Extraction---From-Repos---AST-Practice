# Cluster 17

def pytest_configure(config):
    config.addinivalue_line('markers', 'integration: integration test')
    config.addinivalue_line('markers', 'slow: slow test')

# Node: addinivalue_line
def pytest_configure(config):
    config.addinivalue_line('markers', 'slow: mark test as slow running')
    config.addinivalue_line('markers', 'integration: mark test as integration test')
    config.addinivalue_line('markers', 'unit: mark test as unit test')
    config.addinivalue_line('markers', 'auth: mark test as authentication related')
    config.addinivalue_line('markers', 'upload: mark test as file upload related')
    config.addinivalue_line('markers', 'download: mark test as file download related')
    config.addinivalue_line('markers', 'share: mark test as file sharing related')
    config.addinivalue_line('markers', 'storage: mark test as storage management related')

def pytest_configure(config):
    """
    Configure pytest with custom settings.
    """
    config.addinivalue_line('markers', 'slow: marks tests as slow (deselect with \'-m "not slow"\')')
    config.addinivalue_line('markers', 'integration: marks tests as integration tests')
    config.addinivalue_line('markers', 'api: marks tests as API tests')

def pytest_configure(config):
    config.addinivalue_line('markers', 'slow: mark test as slow')
    config.addinivalue_line('markers', 'integration: mark as integration test')

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line('markers', 'slow: marks tests as slow (deselect with \'-m "not slow"\')')
    config.addinivalue_line('markers', 'integration: marks tests as integration tests')
    config.addinivalue_line('markers', 'security: marks tests as security tests')

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line('markers', 'api: API functionality tests')
    config.addinivalue_line('markers', 'integration: integration tests')
    config.addinivalue_line('markers', 'upload: file upload tests')
    config.addinivalue_line('markers', 'download: file download tests')
    config.addinivalue_line('markers', 'auth: authentication tests')
    config.addinivalue_line('markers', 'edge: edge case tests')
    config.addinivalue_line('markers', 'slow: slow running tests')

def pytest_configure(config):
    config.addinivalue_line('markers', 'slow: marks tests as slow (deselect with \'-m "not slow"\')')
    config.addinivalue_line('markers', 'integration: marks tests as integration tests')
    config.addinivalue_line('markers', 'unit: marks tests as unit tests')

def pytest_configure(config):
    config.addinivalue_line('markers', 'integration: integration tests')
    config.addinivalue_line('markers', 'api: API tests')
    config.addinivalue_line('markers', 'slow: slow tests')

