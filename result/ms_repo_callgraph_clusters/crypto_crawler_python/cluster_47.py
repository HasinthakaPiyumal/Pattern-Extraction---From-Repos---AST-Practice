# Cluster 47

def connect_to_message_queue(host=CACHE_HOST, port=CACHE_PORT):
    global MESSAGE_QUEUE
    MESSAGE_QUEUE = MessageQueue(host, port)
    return MESSAGE_QUEUE

# Node: MessageQueue
