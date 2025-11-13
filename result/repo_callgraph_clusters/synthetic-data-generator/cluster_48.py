# Cluster 48

def test_ndarray_loader(ndarray_list, ndarray_loaders):
    for ndarray_loader in ndarray_loaders:
        subtest_ndarray_loader_function(ndarray_loader, ndarray_list)
        subtest_ndarray_loader_slice(ndarray_loader, ndarray_list)

