# Cluster 12

def pytest_collection_modifyitems(config, items):
    for item in items:
        if 'auth' in item.name:
            item.add_marker(pytest.mark.auth)
        elif 'upload' in item.name:
            item.add_marker(pytest.mark.upload)
        elif 'download' in item.name:
            item.add_marker(pytest.mark.download)
        elif 'share' in item.name:
            item.add_marker(pytest.mark.share)
        elif 'storage' in item.name or 'quota' in item.name:
            item.add_marker(pytest.mark.storage)
        elif 'large' in item.name or 'oversized' in item.name:
            item.add_marker(pytest.mark.slow)
        item.add_marker(pytest.mark.integration)

# Node: add_marker
def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers based on test names.
    """
    for item in items:
        if 'test_task_api' in item.nodeid:
            item.add_marker(pytest.mark.api)
        if 'workflow' in item.name or 'integration' in item.name:
            item.add_marker(pytest.mark.integration)
        if 'pagination' in item.name or 'workflow' in item.name:
            item.add_marker(pytest.mark.slow)

def pytest_collection_modifyitems(config, items):
    for item in items:
        item.add_marker(pytest.mark.integration)

def pytest_collection_modifyitems(config, items):
    for item in items:
        item.add_marker(pytest.mark.integration)
        if 'edge' in item.name:
            item.add_marker(pytest.mark.slow)

