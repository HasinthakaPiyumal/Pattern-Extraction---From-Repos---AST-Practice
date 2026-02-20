# Cluster 44

def get_priority_queue(host=CACHE_HOST, port=CACHE_PORT):
    if PRIORITY_QUEUE is None:
        return connect_to_priority_queue(host, port)
    return PRIORITY_QUEUE

# Node: connect_to_priority_queue
