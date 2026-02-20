# Cluster 45

def connect_to_cache(host=CACHE_HOST, port=CACHE_PORT):
    global LOCAL_CACHE
    LOCAL_CACHE = MemoryCache(host, port)
    return LOCAL_CACHE

# Node: MemoryCache
