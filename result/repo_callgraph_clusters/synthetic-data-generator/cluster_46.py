# Cluster 46

@pytest.fixture
def dataloader_builder(cacher_kwargs):
    yield partial(DataLoader, cacher_kwargs=cacher_kwargs)

