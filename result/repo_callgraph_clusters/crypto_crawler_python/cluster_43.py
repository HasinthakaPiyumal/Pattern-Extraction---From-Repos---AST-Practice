# Cluster 43

def connect_to_priority_queue(host=CACHE_HOST, port=CACHE_PORT):
    global PRIORITY_QUEUE
    PRIORITY_QUEUE = PriorityQueue(host, port)
    return PRIORITY_QUEUE

# Node: PriorityQueue
