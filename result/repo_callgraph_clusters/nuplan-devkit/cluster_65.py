# Cluster 65

def mocked_put_request(**kwargs: Dict[str, Any]) -> MockResponse:
    """Mocks a PUT request that returns the given payload."""
    return MockResponse(kwargs['data'], 200)

