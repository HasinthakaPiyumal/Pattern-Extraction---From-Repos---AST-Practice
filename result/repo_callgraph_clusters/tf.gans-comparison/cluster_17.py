# Cluster 17

def shuffle_batch(tfrecords_list, batch_size, num_threads, num_epochs, min_after_dequeue=None):
    return get_batch(tfrecords_list, batch_size, shuffle=True, num_threads=num_threads, num_epochs=num_epochs, min_after_dequeue=min_after_dequeue)

def batch(tfrecords_list, batch_size, num_threads, num_epochs, min_after_dequeue=None):
    return get_batch(tfrecords_list, batch_size, shuffle=False, num_threads=num_threads, num_epochs=num_epochs, min_after_dequeue=min_after_dequeue)

