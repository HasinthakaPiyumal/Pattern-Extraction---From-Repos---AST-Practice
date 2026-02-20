# Cluster 48

def get_message_queue(host=CACHE_HOST, port=CACHE_PORT):
    if MESSAGE_QUEUE is None:
        return connect_to_message_queue(host, port)
    return MESSAGE_QUEUE

# Node: connect_to_message_queue
