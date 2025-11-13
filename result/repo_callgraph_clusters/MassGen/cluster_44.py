# Cluster 44

def _factory(*args: Any, **kwargs: Any) -> _FakeAnthropicClient:
    client = _FakeAnthropicClient(*args, **kwargs)
    created.append(client)
    return client

