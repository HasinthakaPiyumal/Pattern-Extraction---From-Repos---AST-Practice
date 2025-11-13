# Cluster 50

@pytest.fixture
def base_data_processor():
    d = DataProcessor()
    yield d

