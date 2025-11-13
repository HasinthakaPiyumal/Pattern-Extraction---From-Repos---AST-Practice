# Cluster 7

def get_best_gpu():
    """Dependency: pynvml (for gpu memory informations)
    return type is integer (gpu_id)
    """
    try:
        from pynvml import nvmlInit, nvmlDeviceGetCount, nvmlDeviceGetHandleByIndex, nvmlDeviceGetName, nvmlDeviceGetMemoryInfo
    except Exception as e:
        print('[!] {} => Use default GPU settings ...\n'.format(e))
        return ''
    print('\n===== Check GPU memory =====')

    def to_mb(x):
        return int(x / 1024.0 / 1024.0)
    best_idx = -1
    best_free = 0.0
    nvmlInit()
    n_gpu = nvmlDeviceGetCount()
    for i in range(n_gpu):
        handle = nvmlDeviceGetHandleByIndex(i)
        name = nvmlDeviceGetName(handle)
        mem = nvmlDeviceGetMemoryInfo(handle)
        total = to_mb(mem.total)
        free = to_mb(mem.free)
        used = to_mb(mem.used)
        free_ratio = mem.free / float(mem.total)
        print('{} - {}/{} MB (free: {} MB - {:.2%})'.format(name, used, total, free, free_ratio))
        if free > best_free:
            best_free = free
            best_idx = i
    print('\nSelected GPU is gpu:{}'.format(best_idx))
    print('============================\n')
    return best_idx

def get_batch(tfrecords_list, batch_size, shuffle=False, num_threads=1, min_after_dequeue=None, num_epochs=None):
    name = 'batch' if not shuffle else 'shuffle_batch'
    with tf.variable_scope(name):
        filename_queue = tf.train.string_input_producer(tfrecords_list, shuffle=shuffle, num_epochs=num_epochs)
        data_point = read_parse_preproc(filename_queue)
        if min_after_dequeue is None:
            min_after_dequeue = batch_size * 10
        capacity = min_after_dequeue + 3 * batch_size
        if shuffle:
            batch = tf.train.shuffle_batch(data_point, batch_size=batch_size, capacity=capacity, min_after_dequeue=min_after_dequeue, num_threads=num_threads, allow_smaller_final_batch=True)
        else:
            batch = tf.train.batch(data_point, batch_size, capacity=capacity, num_threads=num_threads, allow_smaller_final_batch=True)
        return batch

def get_batch_join(tfrecords_list, batch_size, shuffle=False, num_threads=1, min_after_dequeue=None, num_epochs=None):
    name = 'batch_join' if not shuffle else 'shuffle_batch_join'
    with tf.variable_scope(name):
        filename_queue = tf.train.string_input_producer(tfrecords_list, shuffle=shuffle, num_epochs=num_epochs)
        example_list = [read_parse_preproc(filename_queue) for _ in range(num_threads)]
        if min_after_dequeue is None:
            min_after_dequeue = batch_size * 10
        capacity = min_after_dequeue + 3 * batch_size
        if shuffle:
            batch = tf.train.shuffle_batch_join(tensors_list=example_list, batch_size=batch_size, capacity=capacity, min_after_dequeue=min_after_dequeue, allow_smaller_final_batch=True)
        else:
            batch = tf.train.batch_join(example_list, batch_size, capacity=capacity, allow_smaller_final_batch=True)
        return batch

