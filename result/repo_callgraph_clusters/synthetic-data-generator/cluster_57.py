# Cluster 57

@pytest.fixture
def data_connector(csv_file):
    yield MockCsvConnector(path=csv_file)

