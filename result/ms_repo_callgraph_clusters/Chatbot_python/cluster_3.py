# Cluster 3

def stream_response(response):
    for word in response.split():
        yield (word + ' ')
        time.sleep(0.05)

# Node: split
# Node: sleep
