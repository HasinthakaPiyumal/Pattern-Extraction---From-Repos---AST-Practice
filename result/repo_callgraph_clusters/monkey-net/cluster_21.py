# Cluster 21

class DataParallelWithCallback(DataParallel):
    """
    Data Parallel with a replication callback.

    An replication callback `__data_parallel_replicate__` of each module will be invoked after being created by
    original `replicate` function.
    The callback will be invoked with arguments `__data_parallel_replicate__(ctx, copy_id)`

    Examples:
        > sync_bn = SynchronizedBatchNorm1d(10, eps=1e-5, affine=False)
        > sync_bn = DataParallelWithCallback(sync_bn, device_ids=[0, 1])
        # sync_bn.__data_parallel_replicate__ will be invoked.
    """

    def replicate(self, module, device_ids):
        modules = super(DataParallelWithCallback, self).replicate(module, device_ids)
        execute_replication_callbacks(modules)
        return modules

def replicate(self, module, device_ids):
    modules = super(DataParallelWithCallback, self).replicate(module, device_ids)
    execute_replication_callbacks(modules)
    return modules

@functools.wraps(old_replicate)
def new_replicate(module, device_ids):
    modules = old_replicate(module, device_ids)
    execute_replication_callbacks(modules)
    return modules

